'use client';

import { useEffect } from 'react';
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
import { CommodityGroup, ParsedOffer } from '@/lib/api';

const orderLineSchema = z.object({
  description: z.string().min(1, 'Description is required'),
  unit_price: z.coerce.number().positive('Price must be positive'),
  amount: z.coerce.number().positive('Amount must be positive'),
  unit: z.string().min(1, 'Unit is required'),
});

const requestFormSchema = z.object({
  title: z.string().min(3, 'Title must be at least 3 characters'),
  vendor_name: z.string().optional(),
  vat_id: z
    .string()
    .optional()
    .refine(
      (val) => !val || /^DE\d{9}$/.test(val),
      'VAT ID must be in format DE + 9 digits (e.g., DE123456789)'
    ),
  commodity_group_id: z.string().optional(),
  department: z.string().optional(),
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
  const { data: commodityGroups, isLoading: loadingGroups } = useCommodityGroups();
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
      order_lines: [{ description: '', unit_price: 0, amount: 1, unit: 'pcs' }],
      ...defaultValues,
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'order_lines',
  });

  // Auto-fill form when parsedOffer changes
  useEffect(() => {
    if (parsedOffer) {
      if (parsedOffer.vendor_name) {
        form.setValue('vendor_name', parsedOffer.vendor_name);
      }
      if (parsedOffer.vat_id) {
        form.setValue('vat_id', parsedOffer.vat_id);
      }
      if (parsedOffer.order_lines && parsedOffer.order_lines.length > 0) {
        form.setValue(
          'order_lines',
          parsedOffer.order_lines.map((line) => ({
            description: line.description,
            unit_price: line.unit_price,
            amount: line.amount,
            unit: line.unit || 'pcs',
          }))
        );
      }
    }
  }, [parsedOffer, form]);

  const calculateTotal = () => {
    const orderLines = form.watch('order_lines');
    return orderLines.reduce((sum, line) => {
      const price = Number(line.unit_price) || 0;
      const amount = Number(line.amount) || 0;
      return sum + price * amount;
    }, 0);
  };

  const handleSuggestCommodity = async () => {
    const title = form.getValues('title');
    const orderLines = form.getValues('order_lines');

    if (!title || orderLines.length === 0) {
      return;
    }

    try {
      const suggestion = await suggestCommodity.mutateAsync({
        title,
        orderLines: orderLines.map((line) => ({
          description: line.description,
          unit_price: Number(line.unit_price),
          amount: Number(line.amount),
          unit: line.unit,
        })),
      });

      if (suggestion.commodity_group_id) {
        form.setValue('commodity_group_id', String(suggestion.commodity_group_id));
      }
    } catch {
      // Error handled by mutation
    }
  };

  // Group commodity groups by category
  const groupedCommodities = commodityGroups?.reduce(
    (acc, group) => {
      const category = group.description?.split(' - ')[0] || 'Other';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(group);
      return acc;
    },
    {} as Record<string, CommodityGroup[]>
  );

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
                <FormLabel>Department</FormLabel>
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
                <FormLabel>Vendor Name</FormLabel>
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
                <FormLabel>VAT ID</FormLabel>
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
            render={({ field }) => (
              <FormItem>
                <FormLabel>Commodity Group</FormLabel>
                <div className="flex gap-2">
                  <Select
                    onValueChange={field.onChange}
                    value={field.value}
                    disabled={loadingGroups}
                  >
                    <FormControl>
                      <SelectTrigger className="flex-1">
                        <SelectValue placeholder="Select a commodity group" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {groupedCommodities &&
                        Object.entries(groupedCommodities).map(([category, groups]) => (
                          <div key={category}>
                            <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                              {category}
                            </div>
                            {groups.map((group) => (
                              <SelectItem key={group.id} value={String(group.id)}>
                                {group.category} - {group.name}
                              </SelectItem>
                            ))}
                          </div>
                        ))}
                    </SelectContent>
                  </Select>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleSuggestCommodity}
                    disabled={suggestCommodity.isPending}
                    title="AI Suggest"
                  >
                    {suggestCommodity.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <FormMessage />
              </FormItem>
            )}
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
                  append({ description: '', unit_price: 0, amount: 1, unit: 'pcs' })
                }
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Line
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {fields.map((field, index) => (
              <div
                key={field.id}
                className="grid gap-4 md:grid-cols-[1fr_120px_100px_100px_40px] items-end"
              >
                <FormField
                  control={form.control}
                  name={`order_lines.${index}.description`}
                  render={({ field }) => (
                    <FormItem>
                      {index === 0 && <FormLabel>Description</FormLabel>}
                      <FormControl>
                        <Input placeholder="Item description" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name={`order_lines.${index}.unit_price`}
                  render={({ field }) => (
                    <FormItem>
                      {index === 0 && <FormLabel>Unit Price</FormLabel>}
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
                      {index === 0 && <FormLabel>Amount</FormLabel>}
                      <FormControl>
                        <Input type="number" placeholder="1" {...field} />
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
                      {index === 0 && <FormLabel>Unit</FormLabel>}
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="pcs">pcs</SelectItem>
                          <SelectItem value="hours">hours</SelectItem>
                          <SelectItem value="days">days</SelectItem>
                          <SelectItem value="kg">kg</SelectItem>
                          <SelectItem value="m">m</SelectItem>
                          <SelectItem value="l">l</SelectItem>
                        </SelectContent>
                      </Select>
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
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}

            <div className="flex justify-end pt-4 border-t">
              <div className="text-lg font-semibold">
                Total: {calculateTotal().toLocaleString('de-DE', {
                  style: 'currency',
                  currency: 'EUR',
                })}
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
