# Updating ninja_metrics.proto

After updating `ninja_metrics.proto`, `ninja_metrics_pb2.py` must be regenerated
using `protoc` with the following steps:

1. Update `ninja_metrics.proto`

2. Generate `ninja_metrics_pb2.py`

    * Install `protoc` if you don’t have `protoc` version 3.11.4. (check using
      `protoc --version`). The newer versions are not compatible with
      `libprotobuf-python` in AOSP. You can download the `protoc` from [the
      github](https://github.com/protocolbuffers/protobuf/releases/tag/v3.11.4)
    * Run the command at
      `development/tools/ninja_dependency_analysis/ninja_metrics_proto`:

      ```
      $ protoc --proto_path=. --python_out=. ninja_metrics.proto
      ```

3. Verification: Run the following command at the source root after building a
   target
    ```
    $ m collect_ninja_inputs
    $ mkdir -p out/dist/logs
    $ out/host/linux-x86/bin/collect_ninja_inputs \
      -n prebuilts/build-tools/linux-x86/bin/ninja \
      -f out/combined-$product.ninja -t vendorimage \
      -m .repo/manifests/default.xml --out out/dist/logs/ninja_inputs
    ```
    , where `$product` is the target product name.

    Check if `ninja_inputs.pb` is generated in the `out/dist/logs` directory.