#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const out = process.argv[2];
if (!out) {
  console.error('usage: node scripts/generate_crypto_fixtures.mjs <output-dir>');
  process.exit(2);
}
fs.mkdirSync(out, { recursive: true });
const write = (name, value) => fs.writeFileSync(path.join(out, name), JSON.stringify(value, null, 2) + '\n', 'utf8');
const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
const { publicKey: wrongPublicKey } = crypto.generateKeyPairSync('ed25519');
const publicPem = publicKey.export({ type: 'spki', format: 'pem' });
const wrongPem = wrongPublicKey.export({ type: 'spki', format: 'pem' });
const message = Buffer.from('Kristal LevelUpDiag signed fixture v1', 'utf8');
const tampered = Buffer.from('Kristal LevelUpDiag signed fixture v2', 'utf8');
const signature = crypto.sign(null, message, privateKey);
const sig = {
  algorithm: 'ed25519',
  public_key_pem: publicPem,
  message_base64: message.toString('base64'),
  signature_base64: signature.toString('base64'),
};
write('signature-valid.json', sig);
write('signature-wrong-key.json', { ...sig, public_key_pem: wrongPem });
write('signature-tampered-message.json', { ...sig, message_base64: tampered.toString('base64') });
const root = {
  key_id: 'levelupdiag-test-root-v1',
  public_key_pem: publicPem,
  not_before: '2026-01-01T00:00:00Z',
  not_after: '2027-01-01T00:00:00Z'
};
const trust = {
  at: '2026-09-16T00:00:00Z',
  key_id: root.key_id,
  algorithm: 'ed25519',
  message_base64: sig.message_base64,
  signature_base64: sig.signature_base64,
  trust_roots: [root],
  revocations: []
};
write('trust-valid.json', trust);
write('trust-revoked.json', { ...trust, revocations: [{ key_id: root.key_id, effective_at: '2026-09-15T00:00:00Z' }] });
write('trust-future-revocation.json', { ...trust, revocations: [{ key_id: root.key_id, effective_at: '2026-09-17T00:00:00Z' }] });
write('trust-expired.json', { ...trust, at: '2027-02-01T00:00:00Z' });
console.log(out);
