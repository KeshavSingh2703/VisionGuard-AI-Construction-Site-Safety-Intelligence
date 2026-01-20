import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Dashboard from '../components/Dashboard';
import Violations from '../components/Violations';
import Reports from '../components/Reports';
import Integrity from '../components/Integrity';
import ChatWidget from '../components/ChatWidget';
import Upload from '../components/Upload';
import Results from '../components/Results';
import SafetyAPI from '../api';

function DashboardLayout() {
    const location = useLocation();
    const navigate = useNavigate();

    // Determine active tab from URL path (remove leading slash)
    // Default to 'dashboard' if root or empty
    // Determine active tab from URL path (remove leading slash)
    const getTabFromPath = () => {
        const path = location.pathname.substring(1);
        return path || 'dashboard';
    };

    const [activeTab, setActiveTab] = useState(getTabFromPath());
    const [currentUploadId, setCurrentUploadId] = useState(null);
    const [loading, setLoading] = useState(true);

    // Sync state with URL changes
    useEffect(() => {
        setActiveTab(location.pathname.substring(1) || 'dashboard');
    }, [location.pathname]);

    // Handle Tab Change (Navigate) - UNUSED REMOVED

    // Data States
    const [summaryData, setSummaryData] = useState(null);
    const [violationsData, setViolationsData] = useState([]);
    const [proximityData, setProximityData] = useState([]);

    const handleUploadComplete = (id) => {
        setCurrentUploadId(id);
        navigate('/results'); // Navigate to results tab via URL
        fetchData(id);
    };

    const fetchData = async (id = null) => {
        // If explicit ID not provided, try to find one or just load default
        // For now, we only fetch if we have an ID to keep it simple, 
        // or maybe fetch latest? 
        // Let's keep strict behavior for now.
        if (!id) {
            // Maybe try to fetch latest from backend if implemented?
            // For now, stop loading.
            setLoading(false);
            return;
        }

        setLoading(true);
        try {
            const [summary, violations, proximity] = await Promise.all([
                SafetyAPI.getSummary(id),
                SafetyAPI.getViolations(id),
                SafetyAPI.getProximityEvents(id)
            ]);

            setSummaryData({
                ...summary,
                validation_status: summary.status === 'PASS' || summary.status === 'completed' ? 'PASS' : summary.status,
                total_images_scanned: summary.total_files,
                compliance_score: summary.accuracy,
                violations_count: Object.values(summary.violations || {}).reduce((a, b) => a + b, 0)
            });
            setViolationsData(violations);
            setProximityData(proximity);
        } catch (err) {
            console.error("Fetch failed", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Initial fetch to populate something if needed
        fetchData();
    }, []);

    const renderContent = () => {
        if (loading && !summaryData && activeTab !== 'upload') {
            return <div className="flex h-64 items-center justify-center text-gray-400">Loading data...</div>;
        }

        switch (activeTab) {
            case 'results':
                return currentUploadId ? <Results uploadId={currentUploadId} /> : <div className="p-8 text-center text-gray-500">Upload a file to see results.</div>;
            case 'dashboard':
                return <Dashboard summary={summaryData} proximity={proximityData} />;
            case 'violations':
                return <Violations violations={violationsData} />;
            case 'reports':
                return <Reports summary={summaryData} uploadId={currentUploadId} />;
            case 'integrity':
                return <Integrity manifest={{ total_files: summaryData?.total_images_scanned || 0 }} />;
            default:
                return <Dashboard summary={summaryData} />;
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Header activeTab={activeTab} onTabChange={setActiveTab} />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <Upload onUploadComplete={handleUploadComplete} />

                {renderContent()}
            </main>
            <ChatWidget />
        </div>
    );
}

export default DashboardLayout;
