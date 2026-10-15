import { get, post, patch } from "./api";

export const fetchCsrf = () => get("/auth/csrf/");
export const fetchMe = () => get("/auth/me/");
export const login = (email, password) => post("/auth/login/", { email, password });
export const register = (payload) => post("/auth/register/", payload);
export const logout = () => post("/auth/logout/");
export const updateProfile = (payload) => patch("/auth/me/", payload);
