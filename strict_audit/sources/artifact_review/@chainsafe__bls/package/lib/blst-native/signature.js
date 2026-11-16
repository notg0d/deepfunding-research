import blst from "@chainsafe/blst";
import { bytesToHex, hexToBytes } from "../helpers/index.js";
import { PointFormat } from "../types.js";
import { PublicKey } from "./publicKey.js";
import { EmptyAggregateError, ZeroSignatureError } from "../errors.js";
export class Signature {
    constructor(value) {
        this.value = value;
    }
    /** @param type Defaults to `CoordType.affine` */
    static fromBytes(bytes, type, validate = true) {
        // need to hack the CoordType so @chainsafe/blst is not a required dep
        const sig = blst.Signature.fromBytes(bytes, validate);
        return new Signature(sig);
    }
    static fromHex(hex) {
        return this.fromBytes(hexToBytes(hex));
    }
    static aggregate(signatures) {
        if (signatures.length === 0) {
            throw new EmptyAggregateError();
        }
        const agg = blst.aggregateSignatures(signatures.map(Signature.convertToBlstSignatureArg));
        return new Signature(agg);
    }
    static verifyMultipleSignatures(sets) {
        return blst.verifyMultipleAggregateSignatures(sets.map((set) => ({
            msg: set.message,
            pk: PublicKey.convertToBlstPublicKeyArg(set.publicKey),
            sig: Signature.convertToBlstSignatureArg(set.signature),
        })));
    }
    static async asyncVerifyMultipleSignatures(sets) {
        return blst.verifyMultipleAggregateSignatures(sets.map((set) => ({
            msg: set.message,
            pk: PublicKey.convertToBlstPublicKeyArg(set.publicKey),
            sig: Signature.convertToBlstSignatureArg(set.signature),
        })));
    }
    static convertToBlstSignatureArg(signature) {
        // Need to cast to blst-native Signature instead of ISignature
        return signature instanceof Uint8Array ? blst.Signature.fromBytes(signature) : signature.value;
    }
    /**
     * Implemented for SecretKey to be able to call .sign()
     */
    static friendBuild(sig) {
        return new Signature(sig);
    }
    verify(publicKey, message) {
        // TODO (@matthewkeil) The note in aggregateVerify and the checks in this method
        // do not seem to go together. Need to check the spec further.
        // Individual infinity signatures are NOT okay. Aggregated signatures MAY be infinity
        try {
            this.value.sigValidate(true);
        }
        catch {
            throw new ZeroSignatureError();
        }
        return blst.verify(message, PublicKey.convertToBlstPublicKeyArg(publicKey), this.value);
    }
    verifyAggregate(publicKeys, message) {
        return blst.fastAggregateVerify(message, publicKeys.map(PublicKey.convertToBlstPublicKeyArg), this.value);
    }
    verifyMultiple(publicKeys, messages) {
        return this.aggregateVerify(publicKeys, messages, false);
    }
    async asyncVerify(publicKey, message) {
        // TODO (@matthewkeil) The note in aggregateVerify and the checks in this method
        // do not seem to go together. Need to check the spec further.
        // Individual infinity signatures are NOT okay. Aggregated signatures MAY be infinity
        try {
            this.value.sigValidate(true);
        }
        catch {
            throw new ZeroSignatureError();
        }
        return blst.verify(message, PublicKey.convertToBlstPublicKeyArg(publicKey), this.value);
    }
    async asyncVerifyAggregate(publicKeys, message) {
        return blst.fastAggregateVerify(message, publicKeys.map(PublicKey.convertToBlstPublicKeyArg), this.value);
    }
    async asyncVerifyMultiple(publicKeys, messages) {
        return this.aggregateVerify(publicKeys, messages, true);
    }
    toBytes(format) {
        if (format === PointFormat.uncompressed) {
            return this.value.toBytes(false);
        }
        else {
            return this.value.toBytes(true);
        }
    }
    toHex(format) {
        return bytesToHex(this.toBytes(format));
    }
    multiplyBy(_bytes) {
        throw new Error("Not implemented");
    }
    aggregateVerify(publicKeys, messages, runAsync) {
        // TODO (@matthewkeil) The note in verify and the checks in this method
        // do not seem to go together. Need to check the spec further.
        // If this set is simply an infinity signature and infinity publicKey then skip verification.
        // This has the effect of always declaring that this sig/publicKey combination is valid.
        // for Eth2.0 specs tests
        if (publicKeys.length === 1) {
            const publicKey = publicKeys[0];
            // eslint-disable-next-line prettier/prettier
            const pk = publicKey instanceof Uint8Array
                ? PublicKey.fromBytes(publicKey)
                : publicKey; // need to cast to blst-native key instead of IPublicKey
            // @ts-expect-error Need to hack type to get access to the private `value`
            if (this.value.isInfinity() && pk.value.isInfinity()) {
                return runAsync ? Promise.resolve(true) : true;
            }
        }
        // blst doesn't expose an async version of aggregateVerify, so we use the sync one
        return blst.aggregateVerify(messages, publicKeys.map(PublicKey.convertToBlstPublicKeyArg), this.value);
    }
}
