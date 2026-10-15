import { get } from "./api";

export const listRooms = (params) => get("/rooms/", params);
export const getRoom = (id, params) => get(`/rooms/${id}/`, params);
export const listCatalog = (kind) => get("/catalog/services/", { kind });
