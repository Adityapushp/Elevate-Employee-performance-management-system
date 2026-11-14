import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { pool } from './pool.js';
const here = path.dirname(fileURLToPath(import.meta.url));
const schemaPath = path.resolve(here, '../../../database/schema.sql');
try {
  const sql = fs.readFileSync(schemaPath, 'utf8');
  await pool.query(sql);
  console.log('Database schema is ready.');
} finally { await pool.end(); }
