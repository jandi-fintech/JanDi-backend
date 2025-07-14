import { configureStore, createSlice } from "@reduxjs/toolkit"

const URL = import.meta.env.VITE_FIN_SERVER_URL || "http://192.168.0.16:8000";

const FIN_SERVER_URL = createSlice({
  name: "finServerUrl",
  initialState: URL,
  reducers: {
    setFinServerUrl: (state, action) => {
      return action.payload;
    }
  }
});

export default configureStore({
  reducer: {
    FIN_SERVER_URL: FIN_SERVER_URL.reducer
  }
});