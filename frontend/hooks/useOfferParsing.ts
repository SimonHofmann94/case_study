'use client';

import { useMutation } from '@tanstack/react-query';
import { offersApi, ParsedOrderLine } from '@/lib/api';

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
    }: {
      title: string;
      orderLines: ParsedOrderLine[];
    }) => offersApi.suggestCommodity(title, orderLines),
  });
}
