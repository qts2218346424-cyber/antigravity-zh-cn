import React from 'react';
import { ProxyMonitor } from '../components/proxy/ProxyMonitor';
import { motion } from 'framer-motion';

const Monitor: React.FC = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="h-full flex flex-col p-5 gap-4 max-w-7xl mx-auto w-full"
        >
            <ProxyMonitor className="flex-1" />
        </motion.div>
    );
};

export default Monitor;