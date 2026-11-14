import jwt from 'jsonwebtoken';
import { query } from '../db/pool.js';
const secret = () => process.env.JWT_SECRET || 'development-only-change-me-before-deploying';
export function signToken(user) {
  return jwt.sign({ sub: String(user.user_id), employee_id: user.employee_id, role: user.role, email: user.email }, secret(), { expiresIn: '8h' });
}
export async function authenticate(req, res, next) {
  try {
    const header = req.headers.authorization || '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : null;
    if (!token) return res.status(401).json({ detail: 'Authentication required. Please sign in.' });
    const payload = jwt.verify(token, secret());
    const result = await query('SELECT user_id, employee_id, email, role, is_active FROM app_users WHERE user_id=$1', [payload.sub]);
    const user = result.rows[0];
    if (!user || !user.is_active) return res.status(401).json({ detail: 'User account is inactive or no longer exists.' });
    req.user = user;
    next();
  } catch { return res.status(401).json({ detail: 'Invalid or expired session. Please sign in again.' }); }
}
export function allowRoles(...roles) {
  return (req, res, next) => roles.includes(req.user?.role) ? next() : res.status(403).json({ detail: 'Your role is not allowed to perform this action.' });
}
