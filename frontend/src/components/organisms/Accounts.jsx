import React from "react";
import AccountRegister from "../molecules/accounts/AccountRegister";
import AccountDetail from "../molecules/accounts/AccountDetail";
import AccountList from "../molecules/accounts/AccountList";
import Divider from "../atoms/Divider";


export default function Accounts() {
  return (
    <>
      <AccountRegister />
      <Divider />
      <AccountList />
      <Divider />
      <AccountDetail />
    </>
  );
}

