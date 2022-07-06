
`./development/tools/ninja_dependency_analysis/collect_inputs.py -n <ninja binary> -f <ninja file> -t <target> -e <exempted_files> -r <repo project file> or -m <repo manifest file>`

For example
`/development/tools/ninja_dependency_analysis/collect_inputs.py -n prebuilts/build-tools/linux-x86/bin/ninja -f out/combined-aosp_cf_x86_64_phone.ninja -t vendorimage -e development/tools/ninja_dependency_analysis/exempted_files -r .repo/project.list`