import React, { useEffect, useState } from "react";
import { 
  Car, 
  Plus, 
  Search, 
  Edit2, 
  Trash2, 
  X, 
  Check, 
  Loader2,
  Tag,
  Settings,
  Info
} from "lucide-react";
import api from "../services/api";

const VehiclePage = () => {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ registrationNumber: "", type: "", model: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    fetchVehicles();
  }, []);

  const fetchVehicles = async () => {
    try {
      setLoading(true);
      const response = await api.get("/vehicles");
      setVehicles(response.data);
    } catch (err) {
      console.error("Error fetching vehicles:", err);
      setError("Failed to load vehicles");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.put(`/vehicles/${editingId}`, formData);
      } else {
        await api.post("/vehicles", formData);
      }
      setIsAdding(false);
      setEditingId(null);
      setFormData({ registrationNumber: "", type: "", model: "" });
      fetchVehicles();
    } catch (err) {
      console.error("Error saving vehicle:", err);
      setError("Failed to save vehicle");
    }
  };

  const handleEdit = (vehicle) => {
    setEditingId(vehicle.id);
    setFormData({ 
      registrationNumber: vehicle.registrationNumber, 
      type: vehicle.type, 
      model: vehicle.model 
    });
    setIsAdding(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this vehicle?")) {
      try {
        await api.delete(`/vehicles/${id}`);
        fetchVehicles();
      } catch (err) {
        console.error("Error deleting vehicle:", err);
        alert("Failed to delete vehicle");
      }
    }
  };

  const filteredVehicles = vehicles.filter(v => 
    v.registrationNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
    v.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    v.model.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-black flex items-center gap-3">
              <Car className="text-cyan-600" size={36} />
              Vehicle Master
            </h1>
            <p className="text-slate-500 mt-2">Manage your fleet and vehicle details</p>
          </div>
          <button
            onClick={() => {
              setIsAdding(true);
              setEditingId(null);
              setFormData({ registrationNumber: "", type: "", model: "" });
            }}
            className="bg-cyan-500 text-black px-4 py-2 rounded-none font-bold uppercase tracking-widest text-xs flex items-center gap-2 hover:bg-black hover:text-white transition-all shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none mr-1"
          >
            <Plus size={20} />
            Add Vehicle
          </button>
        </div>

        {isAdding && (
          <div className="bg-white p-6 rounded-none shadow-sm border border-slate-200 mb-8 transition-all animate-in fade-in slide-in-">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-slate-800">
                {editingId ? "Edit Vehicle" : "New Vehicle"}
              </h2>
              <button onClick={() => setIsAdding(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Registration Number</label>
                <input
                  type="text"
                  required
                  value={formData.registrationNumber}
                  onChange={(e) => setFormData({ ...formData, registrationNumber: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-none focus:ring-2 focus:ring-cyan-500 outline-none uppercase"
                  placeholder="MH 12 AB 1234"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Vehicle Type</label>
                <select
                  required
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-none focus:ring-2 focus:ring-cyan-500 outline-none"
                >
                  <option value="">Select Type</option>
                  <option value="Sedan">Sedan</option>
                  <option value="SUV">SUV</option>
                  <option value="Innova">Innova</option>
                  <option value="Traveller">Traveller</option>
                  <option value="Bus">Bus</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Model Name</label>
                <input
                  type="text"
                  required
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-none focus:ring-2 focus:ring-cyan-500 outline-none"
                  placeholder="e.g. Swift Dzire"
                />
              </div>
              <div className="md:col-span-3 flex justify-end gap-3 mt-2">
                <button
                  type="button"
                  onClick={() => setIsAdding(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-none transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-black text-white px-6 py-2 rounded-none hover:bg-cyan-500 hover:text-black transition-all shadow-sm font-bold uppercase tracking-widest text-xs flex items-center gap-2"
                >
                  <Check size={20} />
                  {editingId ? "Update Vehicle" : "Save Vehicle"}
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="bg-white rounded-none shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                placeholder="Search by reg number or type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-none focus:ring-2 focus:ring-cyan-500 outline-none bg-white"
              />
            </div>
            <div className="text-sm text-slate-500">
              Showing {filteredVehicles.length} vehicles
            </div>
          </div>

          <div className="overflow-x-auto">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="animate-spin text-cyan-500 mb-4" size={40} />
                <p className="text-slate-500">Loading vehicles...</p>
              </div>
            ) : filteredVehicles.length > 0 ? (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Registration #</th>
                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Model</th>
                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredVehicles.map((vehicle) => (
                    <tr key={vehicle.id} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-none bg-cyan-50 flex items-center justify-center text-cyan-600 font-bold text-[10px]">
                            {vehicle.registrationNumber.substring(0, 2)}
                          </div>
                          <span className="font-bold text-slate-800 tracking-wider uppercase">{vehicle.registrationNumber}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-none text-xs font-medium bg-cyan-50 text-cyan-700">
                          <Tag size={12} />
                          {vehicle.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-600">
                        <div className="flex items-center gap-2">
                          <Info size={14} className="text-slate-400" />
                          {vehicle.model}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-4 items-center">
                          <button
                            onClick={() => handleEdit(vehicle)}
                            className="p-1.5 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-none transition-all"
                            title="Edit"
                          >
                            <Edit2 size={16} />
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDelete(vehicle.id); }}
                            className="text-red-600 hover:text-red-700 transition-colors font-bold text-xs"
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
                <Car size={48} className="mx-auto text-slate-200 mb-4" />
                <h3 className="text-lg font-medium text-slate-800">No vehicles found</h3>
                <p className="text-slate-500">Try adjusting your search or add a new vehicle.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VehiclePage;
