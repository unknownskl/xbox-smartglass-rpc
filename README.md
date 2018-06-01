# Xbox RPC server

Open-Source Xbox One RPC server. This project provides a simple http api to send commands to the Xbox One.

Currently implemented:
- Find Xbox devices on the network
- Power on Xbox one
- Shutdown Xbox one
- Launch titles by using a TitleID (ex: spotify:track... / http://www.example.com)
- Control media (Play/Pause/PlayPause/Stop/Next/Previous)

### Environment Variables

| Env         | Default value    |
|-------------|------------------|
| XBOX_IP     | 127.0.0.1        |
| XBOX_LIVEID | FD00000000000000 |

| URI                       | Description                               |
|---------------------------|-------------------------------------------|
| /                         | Returns all api methods available         |
| /api/v1/discovery         | Returns all active Xbox on the network    |
| /api/v1/poweron           | Turn on the Xbox One.                     |
| /api/v1/poweroff          | Turn off the Xbox One.                    |
| /api/v1/launch/{titleid}  | Launch Title on Xbox One (See list below) |
| /api/v1/media             | Returns all media control actions         |
| /api/v1/media/{action}    | Perform media control action              |

### Supported TitleID's
- spotify:track... (Navigate to Spotify and show track)
- http://www.example.com  (Opens edge with the provided url)
- netflix:// (Starts Netflix)

- ms-settings:
- ms-settings:network
- ms-windows-store:navigate?appid=46ee4b2d-7d09-4c09-b4a2-887ab9eb979f (Navigate to Spotify for Xbox)
- ms-windows-store://pdp/?productid=9NFQ49H668TB (Navigate to Spotify for Xbox)
- ms-windows-store://start/?productid=9NFQ49H668TB (Navigate to Spotify for Xbox)
- ms-windows-store://pdp/?productid=9NFQ49H668TB&scenario=click

- appx:Xbox.Dashboard_8wekyb3d8bbwe!Xbox.Dashboard.Application (Go to Dashboard)
- appx:Microsoft.Xbox.Settings_8wekyb3d8bbwe!Xbox.Settings.Application (Launch Settings App)
- appx:SpotifyAB.SpotifyMusic-forXbox_zpdnekdrzrea0!App (Launch Spotify App)
- appx:Microsoft.Xbox.LiveTV_8wekyb3d8bbwe!Microsoft.Xbox.LiveTV.Application (Launch OneGuide / TV)
- appx:XBMCFoundation.Kodi_4n2hpmxwrvr6p!App (Start Kodi)
- appx:Destiny2_z7wx9v9k22rmg!tiger.ReleaseFinal (Launch Destiny 2, yes i am a fan)

- ms-xbl-%08X://media-playback?ContentID=51518722&ContentType=video ???
