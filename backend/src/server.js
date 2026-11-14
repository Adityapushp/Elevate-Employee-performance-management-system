import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import api from './routes/api.js';
import { pool } from './db/pool.js';
dotenv.config();
const app=express();
app.use(helmet());
app.use(cors({origin:(process.env.CORS_ORIGINS||'http://localhost:5173').split(','),credentials:true}));
app.use(express.json({limit:'1mb'}));
app.use('/api/auth/login',rateLimit({windowMs:15*60*1000,max:20,standardHeaders:true,legacyHeaders:false}));
app.use('/api',api);
app.use((err,_req,res,_next)=>{console.error(err);const status=Number(err.status)||500;res.status(status).json({detail:status>=500?'An unexpected server error occurred. Check backend logs.':err.message});});
const port=Number(process.env.PORT||8000);
const server=app.listen(port,()=>console.log(`EPMS API listening on :${port}`));
async function shutdown(){server.close(async()=>{await pool.end();process.exit(0);});}
process.on('SIGTERM',shutdown);process.on('SIGINT',shutdown);
