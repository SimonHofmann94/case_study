'use client';

import { useMutation } from '@tanstack/react-query';
import { offersApi } from '@/lib/api';

export function useParseOffer() {
  return useMutation({
    mutationFn: (file: File) => offersApi.parse(file),
  });
}

export function useParseOfferText() {
  return useMutation({
    mutationFn: (text: string) => offersApi.parseText(text),
  });
}

export function useSuggestCommodity() {
  return useMutation({
    mutationFn: ({
      title,
      orderLines,
      vendorName,
    }: {
      title: string;
      orderLines: Array<{ description: string; unit_price?: number; amount?: number }>;
      vendorName?: string;
    }) => offersApi.suggestCommodity(title, orderLines, vendorName),
  });
}
