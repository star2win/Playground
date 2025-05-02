// honc.dev-compatible DB connection using mssql
import 'dotenv/config';
import sql from 'mssql';

const SQL_DATABASE = process.env.SQL_DATABASE;
const SQL_USERNAME = process.env.SQL_USERNAME;
const SQL_PASSWORD = process.env.SQL_PASSWORD;
const SQL_SERVER = process.env.SQL_SERVER || '192.168.0.7';

console.log(`Database: ${SQL_DATABASE}`);
console.log(`Username: ${SQL_USERNAME}`);
console.log(`Password: ${SQL_PASSWORD}`);
console.log(`Server: ${SQL_SERVER}`);

const config = {
  user: SQL_USERNAME,
  password: SQL_PASSWORD,
  server: SQL_SERVER,
  database: SQL_DATABASE,
  options: {
    encrypt: true,
    trustServerCertificate: true,
  },
  port: 1433,
  connectionTimeout: 30000,
};

export async function handler(event, context) {
  let pool;
  try {
    pool = await sql.connect(config);
    // Query the SM.Customers table
    const result = await pool.request().query('SELECT * FROM [SM].[Customers]');
    console.log(result.recordset);
    return {
      statusCode: 200,
      body: JSON.stringify(result.recordset),
    };
  } catch (err) {
    console.error('MSSQL DB connection error:', err);
    return {
      statusCode: 500,
      body: 'DB connection failed: ' + err.message,
    };
  } finally {
    if (pool) await pool.close();
  }
}

// For local testing only (ESM-compatible)
if (import.meta.url === `file://${process.argv[1]}`) {
  handler({}, {}).then((res) => {
    console.log('Handler result:', res);
  }).catch((err) => {
    console.error('Handler error:', err);
  });
}