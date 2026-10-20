from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from hotel.views import *

urlpatterns = [
	path('admin/'                                          , admin.site.urls                    ),
	path('api/auth/csrf/'                                  , Csrf.as_view()                     , name="csrf_name"),
	path('api/auth/register/'                              , Inscription.as_view()              , name="inscription_name"),
	path('api/auth/login/'                                 , Connexion.as_view()                , name="connexion_name"),
	path('api/auth/logout/'                                , Deconnexion.as_view()              , name="deconnexion_name"),
	path('api/auth/me/'                                    , Moi.as_view()                      , name="moi_name"),
	path('api/rooms/'                                      , ChambreListe.as_view()             , name="chambre_liste_name"),
	path('api/rooms/<int:pk>/'                             , ChambreDetail.as_view()            , name="chambre_detail_name"),
	path('api/catalog/services/'                           , ServiceListe.as_view()             , name="service_liste_name"),
	path('api/reservations/'                               , ReservationListe.as_view()         , name="reservation_liste_name"),
	path('api/reservations/<int:pk>/'                      , ReservationDetail.as_view()        , name="reservation_detail_name"),
	path('api/reservations/<int:pk>/cancel/'               , ReservationAnnulation.as_view()    , name="reservation_annulation_name"),
	path('api/notifications/'                              , NotificationListe.as_view()        , name="notification_liste_name"),
	path('api/notifications/read-all/'                     , NotificationToutLire.as_view()     , name="notification_tout_lire_name"),
	path('api/notifications/<int:pk>/read/'                , NotificationLecture.as_view()      , name="notification_lecture_name"),
	path('api/admin/rooms/'                                , AdminChambreListe.as_view()        , name="admin_chambre_liste_name"),
	path('api/admin/rooms/<int:pk>/'                       , AdminChambreDetail.as_view()       , name="admin_chambre_detail_name"),
	path('api/admin/rooms/<int:pk>/images/'                , AdminChambreImages.as_view()       , name="admin_chambre_images_name"),
	path('api/admin/rooms/<int:pk>/images/<int:image_id>/' , AdminChambreImage.as_view()        , name="admin_chambre_image_name"),
	path('api/admin/services/'                             , AdminServiceListe.as_view()        , name="admin_service_liste_name"),
	path('api/admin/services/<int:pk>/'                    , AdminServiceDetail.as_view()       , name="admin_service_detail_name"),
	path('api/admin/reservations/'                         , AdminReservationListe.as_view()    , name="admin_reservation_liste_name"),
	path('api/admin/reservations/<int:pk>/'                , AdminReservationDetail.as_view()   , name="admin_reservation_detail_name"),
	path('api/admin/reservations/<int:pk>/accept/'         , AdminReservationAction.as_view(), {"action": "accept"}   , name="admin_reservation_accept_name"),
	path('api/admin/reservations/<int:pk>/refuse/'         , AdminReservationAction.as_view(), {"action": "refuse"}   , name="admin_reservation_refuse_name"),
	path('api/admin/reservations/<int:pk>/cancel/'         , AdminReservationAction.as_view(), {"action": "cancel"}   , name="admin_reservation_cancel_name"),
	path('api/admin/reservations/<int:pk>/payments/'       , AdminReservationPaiement.as_view() , name="admin_reservation_paiement_name"),
	path('api/admin/customers/'                            , AdminClientListe.as_view()         , name="admin_client_liste_name"),
	path('api/admin/customers/available-rooms/'            , AdminClientChambresLibres.as_view(), name="admin_client_chambres_libres_name"),
	path('api/admin/customers/<int:pk>/'                   , AdminClientDetail.as_view()        , name="admin_client_detail_name"),
	path('api/admin/stats/'                                , AdminTableauDeBord.as_view()       , name="admin_tableau_de_bord_name"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
