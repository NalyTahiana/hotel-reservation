import { get, post } from "./api";

export const createReservation = (payload) => post("/reservations/", payload);
export const myReservations = (params) => get("/reservations/", params);
export const myInvoice = (id) => get(`/reservations/${id}/invoice/`);
export const cancelMyReservation = (id) => post(`/reservations/${id}/cancel/`);
