import { useState, useEffect } from 'react';
import { Play, RotateCcw } from 'lucide-react';

interface CodeEditorProps {
  code: string;
  language: string;
  onChange: (code: string) => void;
  onSubmit: () => void;
  onReset: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export const CodeEditor = ({
  code,
  language,
  onChange,
  onSubmit,
  onReset,
  disabled = false,
  loading = false,
}: CodeEditorProps) => {
  const [localCode, setLocalCode] = useState(code);

  useEffect(() => {
    setLocalCode(code);
  }, [code]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newCode = e.target.value;
    setLocalCode(newCode);
    onChange(newCode);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Handle Tab key to insert spaces instead of moving focus
    if (e.key === 'Tab') {
      e.preventDefault();
      
      const textarea = e.currentTarget;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const value = textarea.value;
      
      // Default to 2 spaces for indentation (can be customized)
      const tabSize = 2;
      const tabString = ' '.repeat(tabSize);
      
      if (e.shiftKey) {
        // Shift+Tab: Outdent (remove spaces)
        const lines = value.split('\n');
        const lineStart = value.lastIndexOf('\n', start - 1) + 1;
        const lineEnd = value.indexOf('\n', end);
        const actualLineEnd = lineEnd === -1 ? value.length : lineEnd;
        
        // Get the current line
        const lineIndex = value.substring(0, start).split('\n').length - 1;
        const currentLine = lines[lineIndex];
        
        // Remove leading spaces (up to tabSize)
        if (currentLine && currentLine.startsWith(' ')) {
          const spacesToRemove = Math.min(tabSize, currentLine.match(/^ */)?.[0].length || 0);
          const newLine = currentLine.substring(spacesToRemove);
          lines[lineIndex] = newLine;
          
          const newValue = lines.join('\n');
          setLocalCode(newValue);
          onChange(newValue);
          
          // Adjust cursor position
          setTimeout(() => {
            const newStart = Math.max(0, start - spacesToRemove);
            const newEnd = Math.max(0, end - spacesToRemove);
            textarea.setSelectionRange(newStart, newEnd);
          }, 0);
        }
      } else {
        // Tab: Indent
        if (start === end) {
          // Single cursor: insert tab at cursor position
          const newValue = value.substring(0, start) + tabString + value.substring(end);
          setLocalCode(newValue);
          onChange(newValue);
          
          // Move cursor after inserted tab
          setTimeout(() => {
            textarea.setSelectionRange(start + tabSize, start + tabSize);
          }, 0);
        } else {
          // Multiple lines selected: indent all selected lines
          const lines = value.split('\n');
          const lineStart = value.substring(0, start).split('\n').length - 1;
          const lineEnd = value.substring(0, end).split('\n').length - 1;
          
          // Indent selected lines
          for (let i = lineStart; i <= lineEnd; i++) {
            if (lines[i] !== undefined) {
              lines[i] = tabString + lines[i];
            }
          }
          
          const newValue = lines.join('\n');
          setLocalCode(newValue);
          onChange(newValue);
          
          // Adjust selection
          setTimeout(() => {
            const newStart = start + tabSize;
            const newEnd = end + (lineEnd - lineStart + 1) * tabSize;
            textarea.setSelectionRange(newStart, newEnd);
          }, 0);
        }
      }
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">
            Language: <span className="text-purple-600">{language}</span>
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onReset}
            disabled={disabled || loading}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
          <button
            onClick={onSubmit}
            disabled={disabled || loading || !localCode.trim()}
            className="px-4 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
          >
            <Play className="h-4 w-4" />
            {loading ? 'Running...' : 'Run Tests'}
          </button>
        </div>
      </div>
      <div className="flex-1 border rounded-lg overflow-hidden bg-gray-900">
        <textarea
          value={localCode}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled || loading}
          className="w-full h-full p-4 font-mono text-sm text-green-400 bg-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
          style={{
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", Consolas, "source-code-pro", monospace',
            lineHeight: '1.5',
            tabSize: 2,
          }}
          spellCheck={false}
          placeholder="Write your solution here..."
        />
      </div>
      <div className="mt-2 text-xs text-gray-500">
        Tip: Make sure your function returns the expected output type
      </div>
    </div>
  );
};

