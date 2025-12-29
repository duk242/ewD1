This is a python app designed to talk to the Sennheiser ewD1 microphone receivers and display RF Signal, Battery and Audio levels for multiple receivers at once, without requiring the iOS only app.

This repo also has all the information I've gathered on the receivers and protocol used.  The app itself is fairly barebones and is more a proof of concept, but the information here should help anyone wanting to build something better!

# Usage
Requirements:  Should only need the normal stuff that's already installed with python, along with tkinter.

Run with: `python3 ./ewD1.py`

# Communication with the ewD1 Receivers
They use standard ethernet cable and networking. DHCP is on by default, static IP's can be set on the display of the unit.
They use UDP packets on port 45, sending plain text JSON messages which do mention the word "OSC" in there, but it's not a form of OSC I've encountered yet!

See here for a more in depth guide for the different functions available.
# About the Sennheiser ewD1 Receivers
The Sennheiser ew D1 (Evolution Wireless D1) is a digital wireless microphone system that operates in the 2.4 GHz frequency band (license-free worldwide). Released as a bridge between consumer ease-of-use and professional audio quality, it was designed for bands, live sound, and presenters who wanted "set and forget" operation without worrying about complex UHF frequency coordination.

It is fully digital, meaning it does not use an analog compander, resulting in clearer sound and a wider dynamic range compared to older analog systems.

Having used these in community theatre for a couple shows - they're pretty decent. But being in the 2.4ghz range means we're limited in how many we can run, and they do automatic frequency hopping so you don't actually know what frequency they're using (it's a set and pray style system).

> [!NOTE]
> This is not related to the current EW-D system - You cannot use the "Smart Assist App", or Sennheiser WSM (Wireless Systems Manager) with these microphones!
> The naming is kind of confusing.

## Key Details

* Release Date: Announced January 2015 (at the NAMM Show).
* Status: Discontinued in 2021. (It has been effectively succeeded by the EW-D and EW-DX series, which use UHF frequencies instead of 2.4 GHz).
* Frequency Band: 2.4 GHz (2,400 – 2,483.5 MHz).
* Audio Codec: aptX Live (ensures high audio quality with low latency).
* Latency: ~3.9 ms (very low for a digital system of its time).
* Simultaneous Channels: Up to 15 channels theoretical (in ideal conditions), but realistically ~4–8 in Wi-Fi congested environments.
* Control: Ethernet and an onscreen display.  All the options that are available over Ethernet are also available on the on screen display.
* Built in DSP - has built in options for a 7 band EQ, De-Esser, Auto Gain Control and Low Cut Filter.

## Software
The only software you can use to control these remotely is the [Sennheiser WSR (Wireless Remote Control)](https://apps.apple.com/us/app/sennheiser-wsr/id1014458735) app. It's only available on iOS, was last updated 2017-11-30 and is now discontinued.
It is currently (Dec 2025) still available for download and works on iOS only.

# Accessories
Since the system is discontinued, official accessories may be harder to find, but secondary markets often have them.
## Battery Packs (Li-Ion):
* BA 10: Rechargeable battery pack for the handheld transmitter (SKM D1).
* BA 30: Rechargeable battery pack for the bodypack transmitter (SK D1).
* Note: These replaced the standard AA battery sleds and offered longer run times (up to ~11 hours).
## Rack Mount Kit:
* GA 4: Rackmount kit for mounting one or two EM D1 receivers in a 19" rack.
## Microphone Capsules (Handheld):
* Compatible with Sennheiser's standard "evolution" wireless capsules, including e835, e845, e935, e945, and e965.
## Antennas:
* It uses standard Reverse-SMA (R-SMA) connectors (common for WiFi gear, but distinct from the BNC connectors used on Sennheiser UHF gear).

## Belt Pack Mic
The SK D1 belt pack mic uses 2xAA batteries (approx 6 hours run time), with an optional lithium battery pack (BA 30) that'll give you 3.7v 1800mAh for up to 11 hours run time, using USB-C to charge (Approx $50-70AUD).

## Handheld Transmitter (SKM D1)
I haven't used one of these. The model number is SKM D1 if you need one!
