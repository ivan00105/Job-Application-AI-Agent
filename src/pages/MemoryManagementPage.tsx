/**
 * Memory Management Page - View, edit, and delete saved form answers
 */
import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { autofillAPI } from '../api/client';
import { Trash2, Edit2, Plus, Search, Filter, Globe, Building2, Save, X } from 'lucide-react';

interface Memory {
    id: string;
    question_text: string;
    answer_text: string;
    context_key: string;
    company_name: string | null;
    job_url: string | null;
    created_at: string;
    updated_at: string;
}

export const MemoryManagementPage = () => {
    const [memories, setMemories] = useState<Memory[]>([]);
    const [filteredMemories, setFilteredMemories] = useState<Memory[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState<'all' | 'global' | 'company'>('all');
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editAnswer, setEditAnswer] = useState('');
    const [showAddModal, setShowAddModal] = useState(false);
    const [newMemory, setNewMemory] = useState({
        question: '',
        answer: '',
        contextType: 'global' as 'global' | 'company',
        companyName: ''
    });

    useEffect(() => {
        loadMemories();
    }, []);

    useEffect(() => {
        filterMemories();
    }, [memories, searchQuery, filterType]);

    const loadMemories = async () => {
        setLoading(true);
        try {
            const data = await autofillAPI.getMemory();
            setMemories(data.memories || []);
        } catch (error) {
            console.error('Failed to load memories:', error);
            alert('Failed to load memories');
        } finally {
            setLoading(false);
        }
    };

    const filterMemories = () => {
        let filtered = memories;

        // Filter by type
        if (filterType === 'global') {
            filtered = filtered.filter(m => m.context_key === 'global');
        } else if (filterType === 'company') {
            filtered = filtered.filter(m => m.context_key === 'company' || m.company_name);
        }

        // Filter by search query
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(m =>
                m.question_text.toLowerCase().includes(query) ||
                m.answer_text.toLowerCase().includes(query) ||
                (m.company_name && m.company_name.toLowerCase().includes(query))
            );
        }

        setFilteredMemories(filtered);
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this memory?')) {
            return;
        }

        try {
            await autofillAPI.deleteMemory(id);
            setMemories(memories.filter(m => m.id !== id));
        } catch (error) {
            console.error('Failed to delete memory:', error);
            alert('Failed to delete memory');
        }
    };

    const handleEdit = (memory: Memory) => {
        setEditingId(memory.id);
        setEditAnswer(memory.answer_text);
    };

    const handleSaveEdit = async (memory: Memory) => {
        try {
            await autofillAPI.saveAnswer(
                memory.question_text,
                editAnswer,
                memory.context_key === 'global' ? 'global' : 'company',
                memory.company_name || undefined,
                memory.job_url || undefined
            );

            setMemories(memories.map(m =>
                m.id === memory.id ? { ...m, answer_text: editAnswer } : m
            ));
            setEditingId(null);
        } catch (error) {
            console.error('Failed to update memory:', error);
            alert('Failed to update memory');
        }
    };

    const handleCancelEdit = () => {
        setEditingId(null);
        setEditAnswer('');
    };

    const handleAddMemory = async () => {
        if (!newMemory.question.trim() || !newMemory.answer.trim()) {
            alert('Please enter both question and answer');
            return;
        }

        try {
            await autofillAPI.saveAnswer(
                newMemory.question,
                newMemory.answer,
                newMemory.contextType,
                newMemory.companyName || undefined
            );

            await loadMemories();
            setShowAddModal(false);
            setNewMemory({ question: '', answer: '', contextType: 'global', companyName: '' });
        } catch (error) {
            console.error('Failed to add memory:', error);
            alert('Failed to add memory');
        }
    };

    const getUniqueCompanies = () => {
        const companies = memories
            .filter(m => m.company_name)
            .map(m => m.company_name)
            .filter((v, i, a) => a.indexOf(v) === i);
        return companies;
    };

    if (loading) {
        return (
            <Layout>
                <div className="flex justify-center items-center min-h-screen">
                    <div className="text-gray-600">Loading memories...</div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent Memory</h1>
                    <p className="text-gray-600">
                        Manage saved answers for job application forms. These will be used to auto-fill future applications.
                    </p>
                </div>

                {/* Controls */}
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        {/* Search */}
                        <div className="flex-1">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search questions, answers, or companies..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                />
                            </div>
                        </div>

                        {/* Filter */}
                        <div className="flex gap-2">
                            <button
                                onClick={() => setFilterType('all')}
                                className={`px-4 py-2 rounded-lg flex items-center gap-2 ${filterType === 'all'
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                <Filter className="h-4 w-4" />
                                All ({memories.length})
                            </button>
                            <button
                                onClick={() => setFilterType('global')}
                                className={`px-4 py-2 rounded-lg flex items-center gap-2 ${filterType === 'global'
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                <Globe className="h-4 w-4" />
                                Global
                            </button>
                            <button
                                onClick={() => setFilterType('company')}
                                className={`px-4 py-2 rounded-lg flex items-center gap-2 ${filterType === 'company'
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                <Building2 className="h-4 w-4" />
                                Company
                            </button>
                        </div>

                        {/* Add Button */}
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                        >
                            <Plus className="h-4 w-4" />
                            Add Memory
                        </button>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-white rounded-lg shadow-sm p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-purple-100 rounded-lg">
                                <Globe className="h-6 w-6 text-purple-600" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-gray-900">
                                    {memories.filter(m => m.context_key === 'global').length}
                                </div>
                                <div className="text-sm text-gray-600">Global Answers</div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow-sm p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-blue-100 rounded-lg">
                                <Building2 className="h-6 w-6 text-blue-600" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-gray-900">
                                    {memories.filter(m => m.company_name).length}
                                </div>
                                <div className="text-sm text-gray-600">Company-Specific</div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow-sm p-4">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-green-100 rounded-lg">
                                <Filter className="h-6 w-6 text-green-600" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-gray-900">
                                    {getUniqueCompanies().length}
                                </div>
                                <div className="text-sm text-gray-600">Companies</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Memories Table */}
                <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                    {filteredMemories.length === 0 ? (
                        <div className="p-12 text-center">
                            <div className="text-gray-400 mb-4">
                                <Search className="h-12 w-12 mx-auto" />
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No memories found</h3>
                            <p className="text-gray-600">
                                {searchQuery
                                    ? 'Try adjusting your search or filters'
                                    : 'Start auto-filling forms to build your memory bank'}
                            </p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Question
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Answer
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Context
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Updated
                                        </th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Actions
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {filteredMemories.map((memory) => (
                                        <tr key={memory.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="text-sm font-medium text-gray-900">
                                                    {memory.question_text}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                {editingId === memory.id ? (
                                                    <input
                                                        type="text"
                                                        value={editAnswer}
                                                        onChange={(e) => setEditAnswer(e.target.value)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500"
                                                    />
                                                ) : (
                                                    <div className="text-sm text-gray-900 max-w-md truncate">
                                                        {memory.answer_text}
                                                    </div>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {memory.context_key === 'global' ? (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                                        <Globe className="h-3 w-3 mr-1" />
                                                        Global
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                        <Building2 className="h-3 w-3 mr-1" />
                                                        {memory.company_name || 'Company'}
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {new Date(memory.updated_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                {editingId === memory.id ? (
                                                    <div className="flex justify-end gap-2">
                                                        <button
                                                            onClick={() => handleSaveEdit(memory)}
                                                            className="text-green-600 hover:text-green-900"
                                                        >
                                                            <Save className="h-5 w-5" />
                                                        </button>
                                                        <button
                                                            onClick={handleCancelEdit}
                                                            className="text-gray-600 hover:text-gray-900"
                                                        >
                                                            <X className="h-5 w-5" />
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <div className="flex justify-end gap-2">
                                                        <button
                                                            onClick={() => handleEdit(memory)}
                                                            className="text-blue-600 hover:text-blue-900"
                                                        >
                                                            <Edit2 className="h-5 w-5" />
                                                        </button>
                                                        <button
                                                            onClick={() => handleDelete(memory.id)}
                                                            className="text-red-600 hover:text-red-900"
                                                        >
                                                            <Trash2 className="h-5 w-5" />
                                                        </button>
                                                    </div>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Add Memory Modal */}
                {showAddModal && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
                            <h2 className="text-2xl font-bold text-gray-900 mb-4">Add New Memory</h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Question / Field Label
                                    </label>
                                    <input
                                        type="text"
                                        value={newMemory.question}
                                        onChange={(e) => setNewMemory({ ...newMemory, question: e.target.value })}
                                        placeholder="e.g., Desired Salary"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Answer
                                    </label>
                                    <textarea
                                        value={newMemory.answer}
                                        onChange={(e) => setNewMemory({ ...newMemory, answer: e.target.value })}
                                        placeholder="e.g., $80,000"
                                        rows={3}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Context Type
                                    </label>
                                    <select
                                        value={newMemory.contextType}
                                        onChange={(e) =>
                                            setNewMemory({ ...newMemory, contextType: e.target.value as 'global' | 'company' })
                                        }
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                    >
                                        <option value="global">Global (all applications)</option>
                                        <option value="company">Company-specific</option>
                                    </select>
                                </div>

                                {newMemory.contextType === 'company' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Company Name
                                        </label>
                                        <input
                                            type="text"
                                            value={newMemory.companyName}
                                            onChange={(e) => setNewMemory({ ...newMemory, companyName: e.target.value })}
                                            placeholder="e.g., Google"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                        />
                                    </div>
                                )}
                            </div>

                            <div className="mt-6 flex justify-end gap-3">
                                <button
                                    onClick={() => {
                                        setShowAddModal(false);
                                        setNewMemory({ question: '', answer: '', contextType: 'global', companyName: '' });
                                    }}
                                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleAddMemory}
                                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                                >
                                    Add Memory
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
};

