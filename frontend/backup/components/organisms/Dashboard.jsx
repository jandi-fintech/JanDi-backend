import React from "react";
import TransactionsSection from "../molecules/TransactionsSection";
import DomesticPriceSection from "../molecules/DomesticPriceSection";
import OverseasPriceSection from "../molecules/OverseasPriceSection";
import RealtimeSection from "../molecules/RealtimeSection";
import Divider from "../atoms/Divider";

export default function Dashboard() {
  return (
    <section className="bg-white rounded-2xl shadow p-8 space-y-8">
      <h2 className="text-2xl font-bold text-indigo-700 text-center mb-6">API Dashboard</h2>
      <TransactionsSection />
      <Divider />
      <DomesticPriceSection />
      <Divider />
      <OverseasPriceSection />
      <Divider />
      <RealtimeSection />
    </section>
  );
}
