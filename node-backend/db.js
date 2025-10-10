import pkg from 'pg';
import dotenv from 'dotenv';
dotenv.config();

const { Pool } = pkg;

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// Test connection
pool.connect()
  .then(() => console.log("Connected to PostgreSQL!"))
  .catch(err => console.error("DB connection error:", err));
