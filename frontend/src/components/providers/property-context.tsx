"use client";

import * as React from "react";

export const PROPERTIES = [
  { id: 1, name: "Hotel Adriatic Palace" },
] as const;

type PropertyContextValue = {
  propertyId: number;
  setPropertyId: (id: number) => void;
};

const PropertyContext = React.createContext<PropertyContextValue | null>(null);

export function PropertyProvider({ children }: { children: React.ReactNode }) {
  const [propertyId, setPropertyId] = React.useState(1);

  const value = React.useMemo(
    () => ({ propertyId, setPropertyId }),
    [propertyId]
  );

  return (
    <PropertyContext.Provider value={value}>{children}</PropertyContext.Provider>
  );
}

export function useProperty() {
  const ctx = React.useContext(PropertyContext);
  if (!ctx) {
    throw new Error("useProperty must be used within PropertyProvider");
  }
  return ctx;
}
