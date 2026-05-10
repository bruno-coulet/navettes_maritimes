import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Coordonnées approximatives
marseille_lon, marseille_lat = 5.37, 43.30
if_lon, if_lat = 5.325, 43.296
frioul_lon, frioul_lat = 5.312, 43.281

fig = plt.figure(figsize=(8, 8))
ax = plt.axes(projection=ccrs.PlateCarree())

# Définir l'emprise autour de Marseille et des îles
ax.set_extent([5.28, 5.42, 43.26, 43.33], crs=ccrs.PlateCarree())

ax.coastlines(resolution='10m')
ax.gridlines(draw_labels=True)

# Marquer les points d'intérêt
ax.plot(if_lon, if_lat, marker='o', color='red', markersize=8, transform=ccrs.PlateCarree())
ax.text(if_lon + 0.005, if_lat, "Île d'If", fontsize=12, color='red', transform=ccrs.PlateCarree())

ax.plot(frioul_lon, frioul_lat, marker='o', color='blue', markersize=8, transform=ccrs.PlateCarree())
ax.text(frioul_lon + 0.005, frioul_lat, "Frioul", fontsize=12, color='blue', transform=ccrs.PlateCarree())

ax.plot(marseille_lon, marseille_lat, marker='*', color='orange', markersize=10, transform=ccrs.PlateCarree())
ax.text(marseille_lon + 0.005, marseille_lat, "Marseille", fontsize=12, color='orange', transform=ccrs.PlateCarree())

plt.title("Marseille, Île d'If et Frioul")
plt.show()
