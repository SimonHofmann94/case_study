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

        // Debug: Log the raw response from the backend
        console.log('=== Offer Parsing Debug ===');
        console.log('Raw API response:', JSON.stringify(result, null, 2));
        console.log('Order lines:', result.order_lines);
        if (result.order_lines?.[0]) {
          console.log('First order line:', result.order_lines[0]);
          console.log('unit_price:', result.order_lines[0].unit_price);
        }

        // Backend returns parsed offer directly, convert to ParsedOffer format
        if (result.vendor_name || result.order_lines) {
          onParsed({
            vendor_name: result.vendor_name || null,
            vat_id: result.vat_id || null,
            currency: result.currency || 'EUR',
            order_lines: result.order_lines.map((line) => ({
              line_type: line.line_type || 'standard',
              description: line.description,
              detailed_description: line.detailed_description,
              unit_price: line.unit_price,
              amount: line.amount,
              unit: line.unit || 'pcs',
              discount_percent: line.discount_percent,
              discount_amount: line.discount_amount,
              total_price: line.total_price,
            })),
            subtotal_net: result.subtotal_net,
            discount_total: result.discount_total,
            delivery_cost_net: result.delivery_cost_net,
            delivery_tax_amount: result.delivery_tax_amount,
            tax_rate: result.tax_rate,
            tax_amount: result.tax_amount,
            total_gross: result.total_gross,
          });
        } else {
          setError('Failed to parse the document - no data extracted');
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
          ) : file && parseOffer.isSuccess && parseOffer.data?.vendor_name ? (
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

        {parseOffer.isSuccess && parseOffer.data && (
          <div className="mt-4 space-y-2">
            <div className="text-sm text-muted-foreground">
              <p>Format used: {parseOffer.data.format_used}</p>
              {parseOffer.data.token_savings && (
                <p>
                  Token savings: {parseOffer.data.token_savings.savings_percent.toFixed(1)}%
                </p>
              )}
            </div>

            {/* Debug Panel - Extraction Results */}
            <details className="mt-4 border rounded-lg p-3 bg-muted/50">
              <summary className="cursor-pointer font-medium text-sm">
                Debug: View Extraction Results
              </summary>
              <div className="mt-3 space-y-3 text-xs font-mono">
                <div>
                  <strong>Vendor:</strong> {parseOffer.data.vendor_name || 'N/A'}
                </div>
                <div>
                  <strong>VAT ID:</strong> {parseOffer.data.vat_id || 'N/A'}
                </div>
                <div>
                  <strong>Currency:</strong> {parseOffer.data.currency || 'EUR'}
                </div>
                <div>
                  <strong>Order Lines ({parseOffer.data.order_lines?.length || 0}):</strong>
                  <pre className="mt-1 p-2 bg-background rounded border overflow-x-auto">
                    {JSON.stringify(parseOffer.data.order_lines, null, 2)}
                  </pre>
                </div>
                <div>
                  <strong>Totals:</strong>
                  <pre className="mt-1 p-2 bg-background rounded border overflow-x-auto">
{JSON.stringify({
  subtotal_net: parseOffer.data.subtotal_net,
  discount_total: parseOffer.data.discount_total,
  delivery_cost_net: parseOffer.data.delivery_cost_net,
  tax_rate: parseOffer.data.tax_rate,
  tax_amount: parseOffer.data.tax_amount,
  total_gross: parseOffer.data.total_gross,
}, null, 2)}
                  </pre>
                </div>
              </div>
            </details>
          </div>
        )}

      </CardContent>
    </Card>
  );
}
