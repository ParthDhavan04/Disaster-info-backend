import jwt from 'jsonwebtoken';
import User from '../models/User.js';

export const protect = async (req, res, next) => {
    let token;

    if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
        try {
            // Get token from header
            token = req.headers.authorization.split(' ')[1];

            // Verify token
            const decoded = jwt.verify(token, process.env.JWT_SECRET);

            // Get user from the token (exclude password)
            req.user = await User.findById(decoded.id).select('-password');

            if (!req.user) {
                console.log("Protect Middleware: User not found in DB for ID:", decoded.id);
                return res.status(401).json({ message: 'Not authorized, user not found' });
            }

            console.log(`Protect Middleware: Authenticated user ${req.user.email} with role ${req.user.role}`);
            next();
        } catch (error) {
            console.error("Protect Middleware Error:", error.message);
            res.status(401).json({ message: 'Not authorized, token failed' });
        }
    }

    if (!token) {
        res.status(401).json({ message: 'Not authorized, no token' });
    }
};

export const admin = (req, res, next) => {
    if (req.user && req.user.role === 'admin') {
        console.log("Admin Middleware: Access Granted");
        next();
    } else {
        console.log(`Admin Middleware: Access Denied. User role is '${req.user ? req.user.role : 'undefined'}'`);
        res.status(403).json({ message: 'Not authorized as an admin' });
    }
};
