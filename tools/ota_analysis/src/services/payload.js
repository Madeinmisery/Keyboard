/**
 * @fileoverview Class paypload is used to read in and
 * parse the payload.bin file from a OTA.zip file.
 * Class OpType creates a Map that can resolve the
 * operation type.
 * @package zip.js
 * @package protobufjs
 */

import * as zip from '@zip.js/zip.js/dist/zip-full.min.js'
import { chromeos_update_engine as update_metadata_pb } from './update_metadata_pb.js'

const /** string */ _MAGIC = 'CrAU'
const /** Number */ _VERSION_SIZE = 8
const /** Number */ _MANIFEST_LEN_SIZE = 8
const /** Number */ _METADATA_SIGNATURE_LEN_SIZE = 4

const /** @type {Number} */ _PAYLOAD_HEADER_SIZE = _MAGIC.length + _VERSION_SIZE + _MANIFEST_LEN_SIZE + _METADATA_SIGNATURE_LEN_SIZE

const /** Number */ _BRILLO_MAJOR_PAYLOAD_VERSION = 2

class StopIteration extends Error {

}

function readIntAtOffset(buffer, cursor, size) {
  let /** DataView */ view = new DataView(
    buffer.slice(cursor, cursor + size))
  cursor += size
  switch (size) {
  case 2:
    return view.getUInt16(0)
  case 4:
    return view.getUint32(0)
  case 8:
    return Number(view.getBigUint64(0))
  default:
    throw 'Cannot read this integer with size ' + size
  }
}

async function parsePayloadHeader(/** @type {Blob} */buffer) {
  buffer = await buffer.slice(0, _PAYLOAD_HEADER_SIZE).arrayBuffer();
  let /** TextDecoder */ decoder = new TextDecoder()
  let cursor = 0;
  let magic = decoder.decode(
    buffer.slice(0, _MAGIC.length));
  if (magic != _MAGIC) {
    throw new Error('MAGIC is not correct, please double check.');
  }
  cursor += _MAGIC.length;
  const readInt = size => {
    const ret = readIntAtOffset(buffer, cursor, size);
    cursor += size;
    return ret;
  }
  let header_version = readInt(_VERSION_SIZE);
  let manifest_len = readInt(_MANIFEST_LEN_SIZE);

  if (header_version != _BRILLO_MAJOR_PAYLOAD_VERSION) {
    throw new Error("Unexpected major version number: " + header_version)
  }
  let metadata_signature_len = readInt(_METADATA_SIGNATURE_LEN_SIZE)
  return { magic, header_version, manifest_len, metadata_signature_len };
}

class OTAPayloadBlobWriter extends zip.Writer {

  constructor(contentType = "") {
    super();
    this.offset = 0;
    this.contentType = contentType;
    this.blob = new Blob([], { type: contentType });
    this.prefixLength = 0;
  }

  async writeUint8Array(/**  @type {Uint8Array} */ array) {
    // if (this.prefixLength > 0) {
    //   console.log(`Trimming end of array`);
    //   if (array.length + this.offset > this.prefixLength) {
    //     array = array.slice(0, this.prefixLength - this.offset);
    //   }
    // }
    console.log(array.length);
    super.writeUint8Array(array);

    this.blob = new Blob([this.blob, array.buffer], { type: this.contentType });
    this.offset = this.blob.size;
    if (this.prefixLength > 0) {
      console.log(`${this.offset / this.prefixLength}% done`)
    } else if (this.offset >= _PAYLOAD_HEADER_SIZE) {
      const header = await parsePayloadHeader(this.blob);
      this.prefixLength = _PAYLOAD_HEADER_SIZE + header.manifest_len + header.metadata_signature_len;
      console.log(`Metadata size(including header and manifest size) is ${this.prefixLength}`)
    }
    if (this.offset >= this.prefixLength) {
      throw new StopIteration();
    }
  }

  getData() {
    return this.blob;
  }
}

export class Payload {
  /**
   * This class parses the metadata of a OTA package.
   * @param {File} file A OTA.zip file read from user's machine.
   */
  constructor(file) {
    this.packedFile = new zip.ZipReader(new zip.BlobReader(file))
    this.cursor = 0
  }

  async unzipPayload() {
    let /** Array<Entry> */ entries = await this.packedFile.getEntries()
    this.payload = null
    for (let entry of entries) {
      if (entry.filename == 'payload.bin') {
        let writer = new OTAPayloadBlobWriter("");
        try {
          await entry.getData(writer);
        } catch (e) {
          if (e instanceof StopIteration) {
            // Exception used as a hack to stop reading from zip. NO need to do anything
            // Ideally zip.js would provide an API to partialll read a zip
            // entry, but they don't. So this is what we get
          } else {
            throw e;
          }
        }
        this.payload = writer.getData();
        break;
      }
    }
    if (!this.payload) {
      alert('Please select a legit OTA package')
      return
    }
    this.buffer = await this.payload.arrayBuffer();
  }

  /**
   * Read in an integer from binary bufferArray.
   * @param {Int} size the size of a integer being read in
   * @return {Int} an integer.
   */
  readInt(size) {
    let /** DataView */ view = new DataView(
      this.buffer.slice(this.cursor, this.cursor + size))
    this.cursor += size
    switch (size) {
    case 2:
      return view.getUInt16(0)
    case 4:
      return view.getUint32(0)
    case 8:
      return Number(view.getBigUint64(0))
    default:
      throw 'Cannot read this integer with size ' + size
    }
  }

  readHeader() {
    let /** TextDecoder */ decoder = new TextDecoder()
    try {
      this.magic = decoder.decode(
        this.buffer.slice(this.cursor, _MAGIC.length))
      this.cursor += _MAGIC.length
      if (this.magic != _MAGIC) {
        alert('MAGIC is not correct, please double check.')
      }
      this.header_version = this.readInt(_VERSION_SIZE)
      this.manifest_len = this.readInt(_MANIFEST_LEN_SIZE)
      if (this.header_version == _BRILLO_MAJOR_PAYLOAD_VERSION) {
        this.metadata_signature_len = this.readInt(_METADATA_SIGNATURE_LEN_SIZE)
      }
    } catch (err) {
      console.log(err)
      return
    }
  }

  /**
   * Read in the manifest in an OTA.zip file.
   * The structure of the manifest can be found in:
   * aosp/system/update_engine/update_metadata.proto
   */
  readManifest() {
    let /** Array<Uint8> */ manifest_raw = new Uint8Array(this.buffer.slice(
      this.cursor, this.cursor + this.manifest_len
    ))
    this.cursor += this.manifest_len
    this.manifest = update_metadata_pb.DeltaArchiveManifest
      .decode(manifest_raw)
  }

  readSignature() {
    let /** Array<Uint8>*/ signature_raw = new Uint8Array(this.buffer.slice(
      this.cursor, this.cursor + this.metadata_signature_len
    ))
    this.cursor += this.metadata_signature_len
    this.metadata_signature = update_metadata_pb.Signatures
      .decode(signature_raw)
  }

  async init() {
    await this.unzipPayload()
    this.readHeader()
    this.readManifest()
    this.readSignature()
  }

}

export class OpType {
  /**
   * OpType.mapType create a map that could resolve the operation
   * types. The operation types are encoded as numbers in
   * update_metadata.proto and must be decoded before any usage.
   */
  constructor() {
    let /** Array<{String: Number}>*/ types = update_metadata_pb.InstallOperation.Type
    this.mapType = new Map()
    for (let key in types) {
      this.mapType.set(types[key], key)
    }
  }
}

export class MergeOpType {
  /**
   * MergeOpType create a map that could resolve the COW merge operation
   * types. This is very similar to OpType class except that one is for
   * installation operations.
   */
  constructor() {
    let /** Array<{String: Number}>*/ types =
      update_metadata_pb.CowMergeOperation.Type
    this.mapType = new Map()
    for (let key in types) {
      this.mapType.set(types[key], key)
    }
  }
}

export function octToHex(bufferArray, space = true, maxLine = 16) {
  let hex_table = ''
  for (let i = 0; i < bufferArray.length; i++) {
    if (bufferArray[i].toString(16).length === 2) {
      hex_table += bufferArray[i].toString(16) + (space ? ' ' : '')
    } else {
      hex_table += '0' + bufferArray[i].toString(16) + (space ? ' ' : '')
    }
    if ((i + 1) % maxLine == 0) {
      hex_table += '\n'
    }
  }
  return hex_table
}