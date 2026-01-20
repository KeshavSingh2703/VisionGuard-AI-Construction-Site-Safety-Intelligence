import React from 'react';

const StatCard = ({ title, value, subtext, type = 'neutral', icon: Icon }) => {
    const colors = {
        neutral: 'bg-white border-gray-200',
        success: 'bg-green-50 border-green-200 text-green-700',
        warning: 'bg-yellow-50 border-yellow-200 text-yellow-700',
        danger: 'bg-red-50 border-red-200 text-red-700',
    };

    return (
        <div className={`p-6 rounded-xl border shadow-sm ${colors[type]}`}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm font-medium opacity-80 uppercase tracking-wider">{title}</p>
                    <div className="mt-2 flex items-baseline gap-2">
                        <span className="text-3xl font-bold">{value}</span>
                        {subtext && <span className="text-sm opacity-70">{subtext}</span>}
                    </div>
                </div>
                {Icon && <Icon className="w-8 h-8 opacity-60" />}
            </div>
        </div>
    );
};

export default StatCard;
