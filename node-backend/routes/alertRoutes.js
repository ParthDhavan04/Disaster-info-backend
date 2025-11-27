import express from 'express';
import mongoose from 'mongoose';
import { protect, admin } from '../middleware/authMiddleware.js';

const router = express.Router();

// GET /api/alerts - Fetch latest 50 disaster reports
router.get('/', async (req, res) => {
    try {
        // Access the 'reports' collection directly
        const collection = mongoose.connection.collection('reports');

        const alerts = await collection
            .find({})
            .sort({ timestamp: -1 }) // Newest first
            .limit(50) // CRITICAL: Only get the last 50 items
            .toArray();

        res.json(alerts);
    } catch (error) {
        console.error('Error fetching alerts:', error);
        res.status(500).json({ message: 'Server Error fetching alerts' });
    }
});

// DELETE /api/alerts/:id - Delete a disaster report (Admin only)
router.delete('/:id', protect, admin, async (req, res) => {
    try {
        const { id } = req.params;

        // Validate ObjectId format
        if (!mongoose.Types.ObjectId.isValid(id)) {
            return res.status(400).json({ message: 'Invalid ID format' });
        }

        const collection = mongoose.connection.collection('reports');

        console.log(`Attempting to delete report with ID: ${id}`);

        // Convert string id to ObjectId
        const result = await collection.deleteOne({ _id: new mongoose.Types.ObjectId(id) });

        if (result.deletedCount === 0) {
            console.log(`Report with ID ${id} not found in database.`);
            return res.status(404).json({ message: 'Report not found' });
        }

        console.log(`Successfully deleted report ${id}`);
        res.json({ message: 'Report deleted' });
    } catch (error) {
        console.error('Error deleting alert:', error);
        // Return actual error for debugging
        res.status(500).json({ message: `Server Error: ${error.message}` });
    }
});

export default router;
