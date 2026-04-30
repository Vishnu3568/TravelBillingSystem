import React, { useEffect, useState } from "react";
import {
  Building2,
  Plus,
  Search,
  Edit2,
  Trash2,
  X,
  Check,
  Loader2,
  MapPin,
  FileText
} from "lucide-react";
import api from "../services/api";

const CompanyPage = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: "", address: "", gstNumber: "", hasGst: false });
  const [error, setError] = useState("");

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await api.get("/companies");
      setCompanies(response.data);
    } catch (err) {
      console.error("Error fetching companies:", err);
      setError("Failed to load companies");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.put(`/companies/${editingId}`, formData);
      } else {
        await api.post("/companies", formData);
      }
      setIsAdding(false);
      setEditingId(null);
      setFormData({ name: "", address: "", gstNumber: "", hasGst: false });
      fetchCompanies();
    } catch (err) {
      console.error("Error saving company:", err);
      setError("Failed to save company");
    }
  };

  const handleEdit = (company) => {
    setEditingId(company.id);
    setFormData({
      name: company.name,
      address: company.address,
      gstNumber: company.gstNumber,
      hasGst: !!company.gstNumber
    });
    setIsAdding(true);
  };

  const handleDelete = async (id) => {
    console.log("handleDelete called for id:", id);
    if (window.confirm("Are you sure you want to delete this company?")) {
      try {
        await api.delete(`/companies/${id}`);
        fetchCompanies();
      } catch (err) {
        console.error("Error deleting company:", err);
        alert("Failed to delete company");
      }
    }
  };

  const filteredCompanies = companies.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.gstNumber && c.gstNumber.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <Building2 className="text-indigo-600" />
              Company Master
            </h1>
            <p className="text-slate-500">Manage your customer companies and their details</p>
          </div>
          <button
            onClick={() => {
              setIsAdding(true);
              setEditingId(null);
              setFormData({ name: "", address: "", gstNumber: "" });
            }}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-indigo-700 transition-all shadow-md"
          >
            <Plus size={20} />
            Add Company
          </button>
        </div>

        {isAdding && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-8 transition-all animate-in fade-in slide-in-from-top-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-slate-800">
                {editingId ? "Edit Company" : "New Company"}
              </h2>
              <button onClick={() => setIsAdding(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Company Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                  placeholder="e.g. Acme Corp"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="hasGst"
                  checked={formData.hasGst}
                  onChange={(e) => setFormData({ ...formData, hasGst: e.target.checked, gstNumber: e.target.checked ? formData.gstNumber : "" })}
                  className="mr-2 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                />
                <label htmlFor="hasGst" className="text-sm font-medium text-slate-700">Has GST Number?</label>
              </div>
              {formData.hasGst && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">GST Number</label>
                  <input
                    type="text"
                    required
                    value={formData.gstNumber}
                    onChange={(e) => setFormData({ ...formData, gstNumber: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                    placeholder="27AAAAA0000A1Z5"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Address</label>
                <input
                  type="text"
                  required
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                  placeholder="Full Address"
                />
              </div>
              <div className="md:col-span-3 flex justify-end gap-3 mt-2">
                <button
                  type="button"
                  onClick={() => setIsAdding(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-all shadow-sm flex items-center gap-2"
                >
                  <Check size={20} />
                  {editingId ? "Update Company" : "Save Company"}
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                placeholder="Search by name or GST..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
              />
            </div>
            <div className="text-sm text-slate-500">
              Showing {filteredCompanies.length} companies
            </div>
          </div>

          <div className="overflow-x-auto">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="animate-spin text-indigo-600 mb-4" size={40} />
                <p className="text-slate-500">Loading companies...</p>
              </div>
            ) : filteredCompanies.length > 0 ? (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</th>
                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">GST Number</th>
                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Address</th>
                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredCompanies.map((company) => (
                    <tr key={company.id} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
                            <Building2 size={16} />
                          </div>
                          <span className="font-medium text-slate-800">{company.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-slate-600">
                          <FileText size={14} className="text-slate-400" />
                          {company.gstNumber ? company.gstNumber : <span className="text-slate-400 italic">N/A</span>}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-slate-600 max-w-xs truncate">
                          <MapPin size={14} className="text-slate-400" />
                          {company.address}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2 transition-opacity">
                          <button
                            onClick={() => handleEdit(company)}
                            className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                            title="Edit"
                          >
                            <Edit2 size={16} />
                          </button>
                          <button
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); console.log("DEBUG_DELETE_CLICKED", company.id); handleDelete(company.id); }}
                            className="px-3 py-1 bg-red-600 text-white rounded text-xs font-bold hover:bg-red-700 transition-all"
                          >
                            DELETE
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-12">
                <Building2 size={48} className="mx-auto text-slate-200 mb-4" />
                <h3 className="text-lg font-medium text-slate-800">No companies found</h3>
                <p className="text-slate-500">Try adjusting your search or add a new company.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyPage;