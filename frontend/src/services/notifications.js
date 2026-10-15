import { get, post } from "./api";

export const listNotifications = () => get("/notifications/");
export const markNotificationRead = (id) => post(`/notifications/${id}/read/`);
export const markAllNotificationsRead = () => post("/notifications/read-all/");
