'use client';

import { useCallback, useState } from 'react';
import { Upload, FileText, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useParseOffer } from '@/hooks/useOfferParsing';
import { ParsedOffer } from '@/lib/api';

interface FileUploadProps {
  onParsed: (data: ParsedOffer) => void;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = ['application/pdf', 'text/plain'];

export function FileUpload({ onParsed }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const parseOffer = useParseOffer();

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Only PDF and TXT files are allowed';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File size must be less than 10MB';
    }
    return null;
  };

  const handleFile = useCallback(
    async (selectedFile: File) => {
      setError(null);

      const validationError = validateFile(selectedFile);
      if (validationError) {
        setError(validationError);
        return;
      }

      setFile(selectedFile);

      try {
        const result = await parseOffer.mutateAsync(selectedFile);

        if (result.success && result.data) {
          onParsed(result.data);
        } else {
          setError(result.error || 'Failed to parse the document');
        }
      } catch (err) {
        const error = err as { response?: { data?: { detail?: string } } };
        setError(
          error.response?.data?.detail || 'An error occurred while parsing the file'
        );
      }
    },
    [parseOffer, onParsed]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files[0]) {
        handleFile(e.target.files[0]);
      }
    },
    [handleFile]
  );

  const clearFile = useCallback(() => {
    setFile(null);
    setError(null);
    parseOffer.reset();
  }, [parseOffer]);

  return (
    <Card>
      <CardContent className="pt-6">
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-primary/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {parseOffer.isPending ? (
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div>
                <p className="text-lg font-medium">Parsing document...</p>
                <p className="text-sm text-muted-foreground">
                  AI is extracting vendor information
                </p>
              </div>
            </div>
          ) : file && parseOffer.isSuccess ? (
            <div className="flex flex-col items-center gap-4">
              <CheckCircle className="h-12 w-12 text-green-500" />
              <div>
                <p className="text-lg font-medium text-green-700">
                  Document parsed successfully!
                </p>
                <p className="text-sm text-muted-foreground">{file.name}</p>
              </div>
              <Button variant="outline" size="sm" onClick={clearFile}>
                Upload another file
              </Button>
            </div>
          ) : (
            <>
              <input
                type="file"
                id="file-upload"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                onChange={handleChange}
                accept=".pdf,.txt,application/pdf,text/plain"
              />
              <div className="flex flex-col items-center gap-4">
                {file ? (
                  <>
                    <FileText className="h-12 w-12 text-muted-foreground" />
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{file.name}</span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={(e) => {
                          e.preventDefault();
                          clearFile();
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </>
                ) : (
                  <>
                    <Upload className="h-12 w-12 text-muted-foreground" />
                    <div>
                      <p className="text-lg font-medium">
                        Drop your vendor offer here
                      </p>
                      <p className="text-sm text-muted-foreground">
                        or click to browse (PDF or TXT, max 10MB)
                      </p>
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </div>

        {error && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {parseOffer.isSuccess && parseOffer.data?.metadata && (
          <div className="mt-4 text-sm text-muted-foreground">
            <p>
              Format used: {parseOffer.data.metadata.format_used}
              {parseOffer.data.metadata.fallback_used && ' (fallback)'}
            </p>
            {parseOffer.data.metadata.token_savings_percent && (
              <p>
                Token savings: {parseOffer.data.metadata.token_savings_percent.toFixed(1)}%
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
