import express from 'express';
import mongoose from 'mongoose';

const router = express.Router();

// GET /api/alerts - Fetch latest 50 disaster reports
router.get('/', async (req, res) => {
    try {
        // Access the 'reports' collection directly
        // Note: We're not defining a strict Mongoose schema here for flexibility, 
        // but you could define one in a models file if preferred.
        const collection = mongoose.connection.collection('reports');

        const alerts = await collection
            .find({})
            .sort({ timestamp: -1 }) // Sort by timestamp descending (newest first)
            .limit(50)
            .toArray();

        res.json(alerts);
    } catch (error) {
        console.error('Error fetching alerts:', error);
        res.status(500).json({ message: 'Server Error fetching alerts' });
    }
});

export default router;
