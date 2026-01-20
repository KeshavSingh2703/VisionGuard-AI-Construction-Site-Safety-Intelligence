import React from 'react';
import { ShieldCheck, Activity, FileText, Lock } from 'lucide-react';

const Header = ({ activeTab, onTabChange }) => {
    const tabs = [
        { id: 'dashboard', label: 'Dashboard', icon: Activity },
        { id: 'violations', label: 'Violations', icon: ShieldCheck },
        { id: 'reports', label: 'Reports', icon: FileText },
        { id: 'integrity', label: 'Integrity', icon: Lock },
    ];

    return (
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                    <div className="flex items-center gap-3">
                        <div className="bg-blue-600 p-2 rounded-lg">
                            <ShieldCheck className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900 leading-tight">SecureOps</h1>
                            <p className="text-xs text-gray-500 font-medium">Offline Validation Viewer</p>
                        </div>
                    </div>
                    <nav className="flex space-x-1">
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            const isActive = activeTab === tab.id;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => onTabChange(tab.id)}
                                    className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                                            ? 'bg-blue-50 text-blue-700'
                                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                                        }`}
                                >
                                    <Icon className={`w-4 h-4 mr-2 ${isActive ? 'text-blue-700' : 'text-gray-400'}`} />
                                    {tab.label}
                                </button>
                            );
                        })}
                    </nav>
                </div>
            </div>
        </header>
    );
};

export default Header;
