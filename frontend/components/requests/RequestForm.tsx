'use client';

import { useEffect, useRef } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2, Loader2, Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCommodityGroups } from '@/hooks/useCommodityGroups';
import { useSuggestCommodity } from '@/hooks/useOfferParsing';
import { ParsedOffer } from '@/lib/api';

const orderLineSchema = z.object({
  line_type: z.enum(['standard', 'alternative', 'optional']).default('standard'),
  item: z.string().min(1, 'Item name is required'),
  description: z.string().optional(),
  unit_price: z.coerce.number().min(0.01, 'Price must be greater than 0'),
  amount: z.coerce.number().positive('Amount must be positive'),
  unit: z.string().min(1, 'Unit is required'),
  discount_percent: z.coerce.number().min(0).max(100).optional().nullable(),
});

const requestFormSchema = z.object({
  title: z.string().min(3, 'Title must be at least 3 characters'),
  vendor_name: z.string().min(1, 'Vendor name is required'),
  vat_id: z
    .string()
    .min(1, 'VAT ID is required')
    .regex(/^DE\d{9}$/, 'VAT ID must be in format DE + 9 digits (e.g., DE123456789)'),
  commodity_group_id: z.string().min(1, 'Commodity group is required - click "Suggest" to auto-detect'),
  department: z.string().min(1, 'Department is required'),
  notes: z.string().optional(),
  order_lines: z.array(orderLineSchema).min(1, 'At least one order line is required'),
});

export type RequestFormData = z.infer<typeof requestFormSchema>;

interface RequestFormProps {
  onSubmit: (data: RequestFormData) => void;
  isLoading?: boolean;
  defaultValues?: Partial<RequestFormData>;
  parsedOffer?: ParsedOffer | null;
}

export function RequestForm({
  onSubmit,
  isLoading,
  defaultValues,
  parsedOffer,
}: RequestFormProps) {
  const { data: commodityGroups } = useCommodityGroups();
  const suggestCommodity = useSuggestCommodity();

  const form = useForm<RequestFormData>({
    resolver: zodResolver(requestFormSchema),
    defaultValues: {
      title: '',
      vendor_name: '',
      vat_id: '',
      commodity_group_id: '',
      department: '',
      notes: '',
      order_lines: [{ line_type: 'standard', item: '', description: '', unit_price: 0, amount: 1, unit: 'pcs', discount_percent: null }],
      ...defaultValues,
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'order_lines',
  });

  // Track if we've already processed this parsedOffer
  const processedOfferRef = useRef<string | null>(null);

  // Auto-fill form when parsedOffer changes
  useEffect(() => {
    if (parsedOffer) {
      // Create a unique key for this offer to prevent re-processing
      const offerKey = JSON.stringify({
        vendor: parsedOffer.vendor_name,
        lines: parsedOffer.order_lines?.length,
      });

      // Skip if we've already processed this offer
      if (processedOfferRef.current === offerKey) {
        return;
      }
      processedOfferRef.current = offerKey;

      // Debug: Log what we received
      console.log('=== RequestForm Auto-fill Debug ===');
      console.log('parsedOffer:', parsedOffer);

      if (parsedOffer.vendor_name) {
        form.setValue('vendor_name', parsedOffer.vendor_name);
      }
      if (parsedOffer.vat_id) {
        form.setValue('vat_id', parsedOffer.vat_id);
      }
      if (parsedOffer.order_lines && parsedOffer.order_lines.length > 0) {
        const mappedLines = parsedOffer.order_lines.map((line) => ({
          line_type: line.line_type || 'standard',
          item: line.description,  // Short name goes to item
          description: line.detailed_description || '',  // Details go to description
          unit_price: Number(line.unit_price) || 0,
          amount: Number(line.amount) || 1,
          unit: line.unit || 'pcs',
          discount_percent: line.discount_percent ? Number(line.discount_percent) : null,
        }));
        console.log('Mapped lines for form:', mappedLines);
        form.setValue('order_lines', mappedLines);

        // Auto-trigger commodity group suggestion
        const title = form.getValues('title') || 'Procurement Request';
        console.log('=== Triggering Commodity Suggestion ===');
        console.log('Title:', title);
        console.log('Order lines:', parsedOffer.order_lines.length);
        suggestCommodity.mutate({
          title,
          orderLines: parsedOffer.order_lines.map((line) => ({
            description: line.description,
            unit_price: Number(line.unit_price) || 0,
            amount: Number(line.amount) || 1,
          })),
          vendorName: parsedOffer.vendor_name || undefined,
        }, {
          onSuccess: (suggestion) => {
            console.log('=== Commodity Suggestion Response ===');
            console.log('Full suggestion:', suggestion);
            console.log('commodity_group_id:', suggestion.commodity_group_id);
            console.log('category:', suggestion.category);
            console.log('name:', suggestion.name);
            console.log('confidence:', suggestion.confidence);
            if (suggestion.commodity_group_id) {
              const idString = String(suggestion.commodity_group_id);
              console.log('Setting commodity_group_id to:', idString);
              console.log('Available commodity groups:', commodityGroups?.map(g => ({ id: g.id, name: g.name })));
              form.setValue('commodity_group_id', idString, { shouldDirty: true, shouldTouch: true });
            } else {
              console.log('No commodity_group_id returned - not setting field');
              console.log('Suggestion had:', suggestion);
            }
          },
          onError: (error) => {
            console.error('=== Commodity Suggestion Error ===');
            console.error('Error:', error);
          },
        });
      }
    }
  }, [parsedOffer, form, suggestCommodity]);

  const calculateTotal = () => {
    const orderLines = form.watch('order_lines');
    return orderLines
      .filter((line) => line.line_type === 'standard' || !line.line_type)
      .reduce((sum, line) => {
        const price = Number(line.unit_price) || 0;
        const amount = Number(line.amount) || 0;
        const discountPercent = Number(line.discount_percent) || 0;
        const lineTotal = price * amount * (1 - discountPercent / 100);
        return sum + lineTotal;
      }, 0);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Request Title *</FormLabel>
                <FormControl>
                  <Input placeholder="e.g., Office Equipment Purchase" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="department"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Department *</FormLabel>
                <FormControl>
                  <Input placeholder="e.g., Engineering" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="vendor_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Vendor Name *</FormLabel>
                <FormControl>
                  <Input placeholder="e.g., Dell Technologies GmbH" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="vat_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>VAT ID *</FormLabel>
                <FormControl>
                  <Input placeholder="e.g., DE123456789" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="commodity_group_id"
            render={({ field }) => {
              const selectedGroup = commodityGroups?.find(g => String(g.id) === field.value);
              return (
                <FormItem>
                  <FormLabel>Commodity Group *</FormLabel>
                  <div className="flex gap-2">
                    <FormControl>
                      <Input
                        readOnly
                        value={selectedGroup ? `${selectedGroup.category} - ${selectedGroup.name}` : ''}
                        placeholder="Click 'Suggest' to auto-detect"
                        className="bg-muted cursor-not-allowed"
                      />
                    </FormControl>
                    <Button
                      type="button"
                      variant="outline"
                      size="default"
                      disabled={suggestCommodity.isPending || !form.getValues('order_lines')?.some(l => l.item)}
                      onClick={() => {
                        const title = form.getValues('title') || 'Procurement Request';
                        const orderLines = form.getValues('order_lines') || [];
                        const vendorName = form.getValues('vendor_name');

                        suggestCommodity.mutate({
                          title,
                          orderLines: orderLines
                            .filter(line => line.item)
                            .map((line) => ({
                              description: line.item,
                              unit_price: Number(line.unit_price) || 0,
                              amount: Number(line.amount) || 1,
                            })),
                          vendorName: vendorName || undefined,
                        }, {
                          onSuccess: (suggestion) => {
                            console.log('=== Commodity Suggestion Response ===');
                            console.log('Full suggestion:', suggestion);
                            console.log('commodity_group_id:', suggestion.commodity_group_id);
                            if (suggestion.commodity_group_id) {
                              console.log('Setting commodity_group_id to:', String(suggestion.commodity_group_id));
                              form.setValue('commodity_group_id', String(suggestion.commodity_group_id), {
                                shouldValidate: true,
                                shouldDirty: true
                              });
                            } else {
                              console.warn('No commodity_group_id in response!');
                            }
                          },
                          onError: (error) => {
                            console.error('=== Commodity Suggestion Error ===');
                            console.error('Error:', error);
                          },
                        });
                      }}
                    >
                      {suggestCommodity.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4 mr-1" />
                          Suggest
                        </>
                      )}
                    </Button>
                  </div>
                  <FormMessage />
                </FormItem>
              );
            }}
          />
        </div>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Order Lines</CardTitle>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  append({ line_type: 'standard', item: '', description: '', unit_price: 0, amount: 1, unit: 'pcs', discount_percent: null })
                }
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Line
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {fields.map((field, index) => {
              const lineType = form.watch(`order_lines.${index}.line_type`);
              return (
                <div
                  key={field.id}
                  className={`p-4 border rounded-lg space-y-4 ${
                    lineType === 'alternative' ? 'border-blue-300 bg-blue-50/50' :
                    lineType === 'optional' ? 'border-amber-300 bg-amber-50/50' : ''
                  }`}
                >
                  {/* Row 1: Type + Item + Delete */}
                  <div className="flex gap-4 items-start">
                    <FormField
                      control={form.control}
                      name={`order_lines.${index}.line_type`}
                      render={({ field }) => (
                        <FormItem className="w-32">
                          <FormLabel className={index === 0 ? '' : 'sr-only'}>Type</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="standard">Standard</SelectItem>
                              <SelectItem value="alternative">Alternative</SelectItem>
                              <SelectItem value="optional">Optional</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name={`order_lines.${index}.item`}
                      render={({ field }) => (
                        <FormItem className="flex-1">
                          <FormLabel className={index === 0 ? '' : 'sr-only'}>Item *</FormLabel>
                          <FormControl>
                            <Input placeholder="Item name (e.g., Dell XPS 15)" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => fields.length > 1 && remove(index)}
                      disabled={fields.length <= 1}
                      className="text-destructive hover:text-destructive mt-6"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Row 2: Description (optional details) */}
                  <FormField
                    control={form.control}
                    name={`order_lines.${index}.description`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className={index === 0 ? '' : 'sr-only'}>Description (optional)</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Detailed specifications, features, etc."
                            className="min-h-[60px]"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Row 3: Price, Amount, Unit, Discount */}
                  <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
                    <FormField
                      control={form.control}
                      name={`order_lines.${index}.unit_price`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className={index === 0 ? '' : 'sr-only'}>Unit Price *</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              step="0.01"
                              placeholder="0.00"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name={`order_lines.${index}.amount`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className={index === 0 ? '' : 'sr-only'}>Amount *</FormLabel>
                          <FormControl>
                            <Input type="number" step="0.01" placeholder="1" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name={`order_lines.${index}.unit`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className={index === 0 ? '' : 'sr-only'}>Unit *</FormLabel>
                          <FormControl>
                            <Input placeholder="pcs, m², Stk, etc." {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name={`order_lines.${index}.discount_percent`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className={index === 0 ? '' : 'sr-only'}>Discount %</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              step="0.1"
                              placeholder="0"
                              {...field}
                              value={field.value ?? ''}
                              onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>
              );
            })}

            <div className="pt-4 border-t space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Subtotal (net)</span>
                <span>
                  {(parsedOffer?.subtotal_net ?? calculateTotal()).toLocaleString('de-DE', {
                    style: 'currency',
                    currency: parsedOffer?.currency || 'EUR',
                  })}
                </span>
              </div>
              {parsedOffer?.discount_total && Number(parsedOffer.discount_total) > 0 && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>Discount</span>
                  <span>
                    -{Number(parsedOffer.discount_total).toLocaleString('de-DE', {
                      style: 'currency',
                      currency: parsedOffer?.currency || 'EUR',
                    })}
                  </span>
                </div>
              )}
              {parsedOffer?.delivery_cost_net && Number(parsedOffer.delivery_cost_net) > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">
                    Delivery
                    {parsedOffer?.delivery_tax_amount && Number(parsedOffer.delivery_tax_amount) > 0 && (
                      <span className="text-xs ml-1">
                        (incl. {Number(parsedOffer.delivery_tax_amount).toLocaleString('de-DE', { style: 'currency', currency: parsedOffer?.currency || 'EUR' })} tax)
                      </span>
                    )}
                  </span>
                  <span>
                    {Number(parsedOffer.delivery_cost_net).toLocaleString('de-DE', {
                      style: 'currency',
                      currency: parsedOffer?.currency || 'EUR',
                    })}
                  </span>
                </div>
              )}
              {(parsedOffer?.tax_amount || parsedOffer?.tax_rate) && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">
                    Tax {parsedOffer?.tax_rate ? `(${Number(parsedOffer.tax_rate)}%)` : ''}
                  </span>
                  <span>
                    {parsedOffer?.tax_amount
                      ? Number(parsedOffer.tax_amount).toLocaleString('de-DE', {
                          style: 'currency',
                          currency: parsedOffer?.currency || 'EUR',
                        })
                      : '-'}
                  </span>
                </div>
              )}
              <div className="flex justify-between text-lg font-semibold pt-2 border-t">
                <span>Total (gross)</span>
                <span>
                  {(parsedOffer?.total_gross ?? calculateTotal()).toLocaleString('de-DE', {
                    style: 'currency',
                    currency: parsedOffer?.currency || 'EUR',
                  })}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Any additional notes or comments..."
                  className="min-h-[100px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-4">
          <Button type="submit" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Request'
            )}
          </Button>
        </div>
      </form>
    </Form>
  );
}
