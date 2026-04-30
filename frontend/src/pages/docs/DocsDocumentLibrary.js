import { Link } from 'react-router-dom';
import { ArrowRight, FileText, FolderOpen, Upload, Download, Search, Tag, Share2, Lock, CheckCircle } from 'lucide-react';

export default function DocsDocumentLibrary() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <FolderOpen className="h-4 w-4" /> Core Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Document Library</h1>
        <p className="text-lg text-gray-400">
          The Document Library is your central hub for storing, organizing, and sharing all business documents, templates, artwork, and files.
        </p>
      </div>

      {/* What You Can Store */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-cyan-400" /> What You Can Store
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
              <span>Artwork files (AI, PSD, PDF, PNG, etc.)</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
              <span>Customer logos and brand assets</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
              <span>Quote and invoice templates</span>
            </li>
          </ul>
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
              <span>Questionnaire templates</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
              <span>Contracts and agreements</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
              <span>Reference materials and specs</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Uploading Documents */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Upload className="h-5 w-5 text-cyan-400" /> Uploading Documents
        </h2>
        <ol className="space-y-3">
          {[
            'Go to Documents in the main navigation',
            'Click the "+ Upload" button',
            'Select files from your computer (or drag and drop)',
            'Add tags and categories to organize',
            'Choose visibility: Internal Only or Share with Customer',
            'Click Upload to save'
          ].map((step, index) => (
            <li key={index} className="flex items-start gap-3 text-gray-300">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{index + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Organization */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <FolderOpen className="h-5 w-5 text-cyan-400" /> Organization Features
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium text-white mb-2">Folders</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Create nested folder structures</li>
              <li>• Organize by customer, project, or type</li>
              <li>• Move files between folders easily</li>
              <li>• Rename and delete folders</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-white mb-2">Tags & Categories</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Add multiple tags to any document</li>
              <li>• Filter by tag for quick finding</li>
              <li>• Pre-defined categories for shop docs: Artwork, Templates, Contracts, Quotes, Permits, Insurance, Warranty, etc.</li>
              <li>• <strong className="text-white">AI tool outputs auto-tag</strong> into matching categories: Logo Concept, Brand Kit, Tagline, Social Post, Content Calendar, Campaign Plan, Blog Article, Marketing Content</li>
              <li>• Create custom tags</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Search className="h-5 w-5 text-cyan-400" /> Search & Filter
        </h2>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Text Search</strong> — Find documents by name or content</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Filter by Type</strong> — Show only PDFs, images, or other file types</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Filter by Tag</strong> — Narrow down by assigned tags</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Date Range</strong> — Find documents from specific time periods</span>
          </li>
        </ul>
      </div>

      {/* Sharing & Permissions */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Share2 className="h-5 w-5 text-blue-400" /> Sharing & Permissions
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium text-white mb-2 flex items-center gap-2">
              <Lock className="h-4 w-4 text-amber-400" /> Internal Only
            </h3>
            <p className="text-sm text-gray-300">
              Default setting. Documents are only visible to your team members. Customers cannot see these files.
            </p>
          </div>
          <div>
            <h3 className="font-medium text-white mb-2 flex items-center gap-2">
              <Share2 className="h-4 w-4 text-green-400" /> Share with Customer
            </h3>
            <p className="text-sm text-gray-300">
              Documents marked for sharing appear in the Customer Portal. Customers can view and download.
            </p>
          </div>
        </div>
      </div>

      {/* Link to Jobs */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Tag className="h-5 w-5 text-cyan-400" /> Linking Documents to Jobs
        </h2>
        <ul className="space-y-2 text-gray-300">
          <li>• Documents can be linked to specific orders or order items</li>
          <li>• Upload artwork directly from the Order Detail page</li>
          <li>• Linked documents appear in the order's Files tab</li>
          <li>• Questionnaire responses are automatically saved as documents</li>
          <li>• Easy to find all files related to a project</li>
        </ul>
      </div>

      {/* Questionnaire Templates */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-cyan-400" /> Questionnaire Templates
        </h2>
        <p className="text-gray-300 mb-3">Create reusable forms for gathering customer information:</p>
        <ul className="space-y-2 text-gray-300">
          <li>• <strong className="text-white">Vehicle Wrap Intake</strong> — Vehicle measurements, coverage preferences</li>
          <li>• <strong className="text-white">Event Signs</strong> — Event details, quantities, dates</li>
          <li>• <strong className="text-white">Design Brief</strong> — Brand guidelines, preferences, requirements</li>
          <li>• <strong className="text-white">Custom Templates</strong> — Build your own questionnaires</li>
        </ul>
        <p className="text-gray-400 text-sm mt-3">
          Questionnaires can be assigned to customers through the portal. Responses are saved back to the Document Library.
        </p>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/customers" className="text-gray-400 hover:text-white">← Customers</Link>
        <Link to="/docs/quotes-jobs" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Orders & Order Items <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
