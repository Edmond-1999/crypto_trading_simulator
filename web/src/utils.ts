import type { Balance, Order } from "./types";

type ApiError = {
  error?: string;
  message?: string;
};

export async function readApiResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let data: unknown = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { message: text };
    }
  }

  if (!response.ok) {
    const errorData = data as ApiError;
    throw new Error(
      errorData.message ||
        errorData.error ||
        `Request failed with status ${response.status}.`,
    );
  }

  return data as T;
}

export function positivePrice(value: unknown): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) && number > 0 ? number : null;
}

export function balanceTotal(balance: Balance): number {
  const total =
    typeof balance.total === "string" && balance.total.trim() !== ""
      ? Number(balance.total)
      : Number.NaN;

  if (Number.isFinite(total)) {
    return total;
  }

  const available =
    typeof balance.available === "string" &&
    balance.available.trim() !== ""
      ? Number(balance.available)
      : Number.NaN;

  return Number.isFinite(available) ? available : 0;
}

export function money(value: number | string, currency = "USD", digits = 2) {
  const number = Number(value);

  if (!Number.isFinite(number)) return `${currency} —`;

  return `${currency} ${number.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

export function quantityFormat(value: number | string, digits = 8) {
  const number = Number(value);

  if (!Number.isFinite(number)) return "0";

  return number.toLocaleString("en-US", {
    maximumFractionDigits: digits,
  });
}

export function shortDate(value?: string) {
  if (!value) return "Date unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString();
}

export function orderQuoteCurrency(order: Order) {
  return (
    order.quote_currency ||
    (order.quote_asset_id ? `Asset #${order.quote_asset_id}` : "Quote")
  );
}
