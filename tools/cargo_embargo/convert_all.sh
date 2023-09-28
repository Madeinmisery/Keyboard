#!/bin/bash

set -e

report="cargo_embargo_report.html"

cat > $report <<END
<html>
<head>
<title>cargo_embargo crate report</title>
<style type="text/css">
td { vertical-align: top; }
.success { color: green; }
.skipped { color: yellow; }
.warning { color: orange; }
.error { color: red; }
</style>
</head>
<body>
<h1>cargo_embargo crate report</h1>
<h2>Using existing cargo_embargo.json</h2>
<table>
<tr><th>Crate name</th><th>Generate</th><th>Details</th><th style="width: 25%;">Files</th></tr>
END

success_count=0
different_count=0
total_count=0
for new_config in */cargo_embargo.json; do
  ((total_count+=1))
  crate=$(dirname $new_config)
  echo "Trying $crate..."
  echo "<tr><td><code>$crate</code></td>" >> $report
  if (cd $crate && cargo_embargo generate cargo_embargo.json) 2> cargo_embargo.err; then
    (cd $crate && git diff Android.bp > Android.bp.diff)
    if grep "WARNING" cargo_embargo.err; then
      echo '<td class="error">Warning</td><td></td>' >> $report
      echo '<td><details><summary>' >> $report
      grep -m 1 "WARNING" cargo_embargo.err >> $report
      echo '</summary>' >> $report
      sed 's/$/<br\/>/g' < cargo_embargo.err >> $report
      echo '</details></td>' >> $report
    else
      # Compare the checked-in Android.bp to the generated one.
      (cd $crate && git show HEAD:Android.bp > Android.bp.orig)
      if diff $crate/Android.bp.orig $crate/Android.bp > /dev/null; then
        echo '<td class="success">Success</td>' >> $report
        ((success_count+=1))
      else
        echo '<td class="warning">Different</td>' >> $report
        ((different_count+=1))
      fi

      echo '<td>' >> $report
      if [[ -s "cargo_embargo.err" ]]; then
        echo '<details>' >> $report
        sed 's/$/<br\/>/g' < cargo_embargo.err >> $report
        echo '</details>' >> $report
      fi
      echo '</td>' >> $report
    fi
  else
    echo '<td class="error">Error</td><td></td>' >> $report
    echo '<td><details open>' >> $report
    sed 's/$/<br\/>/g' < cargo_embargo.err >> $report
    echo '</details></td>' >> $report
  fi

  rm cargo_embargo.err
  rm -rf "$crate/cargo.metadata" "$crate/cargo.out" "$crate/target.tmp" "$crate/Cargo.lock" "$crate/Android.bp.orig" "$crate/Android.bp.embargo" "$crate/Android.bp.embargo_nobuild"
  (cd $crate && git checkout Android.bp)

  echo '<td>' >> $report
  if [[ -s "$crate/Android.bp.diff" ]]; then
    echo '<details><summary>Android.bp.diff</summary><pre>' >> $report
    cat "$crate/Android.bp.diff" >> $report
    echo '</pre></details>' >> $report
    rm "$crate/Android.bp.diff"
  fi
  echo '</td></tr>' >> $report
done

echo '</table>' >> $report
echo "<p>$success_count success, $different_count different, $total_count total.</p>" >> $report

cat >> $report <<END
<h2>Converting cargo2android.json</h2>
<table>
<tr><th>Crate name</th><th>Convert</th><th>Generate</th><th>Generate without build</th><th>Details</th><th style="width: 25%;">Files</th></tr>
END

total_count=0
convert_count=0
convert_error_count=0
generate_error_count=0
generate_success_count=0
generate_without_build_error_count=0
generate_without_build_success_count=0
for old_config in */cargo2android.json; do
  ((total_count+=1))
  crate=$(dirname $old_config)
  echo "Trying $crate..."
  echo "<tr><td><code>$crate</code></td>" >> $report
  if cargo_embargo convert $old_config $crate > $crate/cargo_embargo.json 2> cargo_embargo.err; then
    echo "$crate: Success"

    echo '<td class="success">Success</td>' >> $report
    ((convert_count+=1))

    if (cd $crate && cargo_embargo generate cargo_embargo.json) 2> cargo_embargo.err; then
      (cd $crate && git diff Android.bp > Android.bp.diff)
      if grep "WARNING" cargo_embargo.err; then
        echo '<td class="error">Warning</td><td></td>' >> $report
        echo '<td><details><summary>' >> $report
        grep -m 1 "WARNING" cargo_embargo.err >> $report
        echo '</summary>' >> $report
        sed 's/$/<br\/>/g' < cargo_embargo.err >> $report
        echo '</details></td>' >> $report
      else
        # Compare a cleaned-up checked-in Android.bp to the generated one.
        (cd $crate && git show HEAD:Android.bp | grep -Ev '^ *// ' | grep -Ev '^$' > Android.bp.orig)
        bpfmt -w $crate/Android.bp.orig
        # Skip comments and blank lines, and force rustlibs to be multi-line like cargo2android.py.
        cat $crate/Android.bp | grep -v '^// ' | grep -Ev '^$' | sed 's/rustlibs: \["/rustlibs: \[\n"/g' > $crate/Android.bp.embargo
        bpfmt -w $crate/Android.bp.embargo
        if diff $crate/Android.bp.orig $crate/Android.bp.embargo > /dev/null; then
          echo '<td class="success">Success</td>' >> $report
          ((generate_success_count+=1))
        else
          echo '<td class="warning">Different</td>' >> $report
        fi

        # Try in metadata-only mode.
        cargo_embargo convert --no-build $old_config $crate > $crate/cargo_embargo_nobuild.json 2> /dev/null
        if (cd $crate && cargo_embargo generate cargo_embargo_nobuild.json) 2> cargo_embargo_nobuild.err; then
          (cd $crate && git diff Android.bp > Android.bp.diff_nobuild)
          cat $crate/Android.bp | grep -Ev '^ *// ' | grep -Ev '^$' | sed 's/rustlibs: \["/rustlibs: \[\n"/g' > $crate/Android.bp.embargo_nobuild
          bpfmt -w $crate/Android.bp.embargo_nobuild
          if diff $crate/Android.bp.orig $crate/Android.bp.embargo_nobuild > /dev/null; then
            echo '<td class="success">Success</td>' >> $report
            ((generate_without_build_success_count+=1))
          else
            echo '<td class="warning">Different</td>' >> $report
          fi
          mv $crate/cargo_embargo_nobuild.json $crate/cargo_embargo.json
        else
          echo '<td class="error">Error</td>' >> $report
          ((generate_without_build_error_count+=1))
          rm $crate/cargo_embargo_nobuild.json
        fi

        echo '<td>' >> $report
        if [[ -s "cargo_embargo.err" ]]; then
          echo '<details>' >> $report
          sed 's/$/<br\/>/g' < cargo_embargo.err >> $report
          echo '</details>' >> $report
        fi
        if [[ -s "cargo_embargo_nobuild.err" ]]; then
          echo '<details>' >> $report
          sed 's/$/<br\/>/g' < cargo_embargo_nobuild.err >> $report
          echo '</details>' >> $report
        fi
        echo '</td>' >> $report
      fi
    else
      echo '<td class="error">Error</td><td></td>' >> $report
      ((generate_error_count+=1))
      echo '<td><details open>' >> $report
      sed 's/$/<br\/>/g' < cargo_embargo.err >> $report
      echo '</details></td>' >> $report
    fi
  else
    echo "***Error converting $crate:***"
    cat cargo_embargo.err
    cat $old_config

    # Remove empty config immediately, so it doesn't get included in report.
    rm "$crate/cargo_embargo.json"

    ((convert_error_count+=1))

    echo '<td class="error">Error</td><td></td><td></td><td><details>' >> $report
    echo '<summary>' >> $report
    grep "unknown field" cargo_embargo.err | sed 's/, expected.*$//g' >> $report
    echo '</summary>' >> $report
    sed 's/$/<br\/>/g' < cargo_embargo.err >> $report
    echo '</details></td>' >> $report
  fi

  rm -f cargo_embargo.err cargo_embargo_nobuild.err
  rm -rf "$crate/cargo.metadata" "$crate/cargo.out" "$crate/target.tmp" "$crate/Cargo.lock" "$crate/Android.bp.orig" "$crate/Android.bp.embargo" "$crate/Android.bp.embargo_nobuild"
  #(cd $crate && git checkout Android.bp)

  echo '<td><details><summary>cargo2android.json</summary><code>' >> $report
  cat $old_config >> $report
  echo '</code></details>' >> $report
  if [[ -f "$crate/cargo_embargo.json" ]]; then
    echo '<details><summary>cargo_embargo.json</summary><code>' >> $report
    cat "$crate/cargo_embargo.json" >> $report
    echo '</code></details>' >> $report
    rm "$crate/cargo_embargo.json"
  fi
  if [[ -f "$crate/Android.bp.diff" ]]; then
    echo '<details><summary>Android.bp.diff</summary><pre>' >> $report
    cat "$crate/Android.bp.diff" >> $report
    echo '</pre></details>' >> $report
    rm "$crate/Android.bp.diff"
  fi
  if [[ -f "$crate/Android.bp.diff_nobuild" ]]; then
    echo '<details><summary>Android.bp.diff_nobuild</summary><pre>' >> $report
    cat "$crate/Android.bp.diff_nobuild" >> $report
    echo '</pre></details>' >> $report
    rm "$crate/Android.bp.diff_nobuild"
  fi
  echo '</td></tr>' >> $report
done

echo '</table>' >> $report

echo "<p>$total_count crates, $convert_count converted, $convert_error_count errors converting, $generate_error_count errors generating with build, $generate_success_count successfully generated with build, $generate_without_build_error_count errors generating without build, $generate_without_build_success_count successfully generated without build</p>" >> $report

cat >> $report <<END
</body>
</html>
END

echo "Open file://$PWD/$report for details"
