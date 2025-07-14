import React from "react";
import TransactionsSection from "../molecules/investments/TransactionsSection";
import DomesticPriceSection from "../molecules/investments/DomesticPriceSection";
import OverseasPriceSection from "../molecules/investments/OverseasPriceSection";
import RealtimeSection from "../molecules/investments/RealtimeSection";
import Divider from "../atoms/Divider";

export default function Investments() {
  return (
    <>
      <DomesticPriceSection />
      <Divider />
      <OverseasPriceSection />
      <Divider />
      <RealtimeSection />
    </>
  );
}
