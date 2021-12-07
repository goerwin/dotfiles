Download the repo and copy all your dotfiles inside src into your `<homeDir>` using:

```sh
$ zsh install.zsh <homeDir>
```

To update ShareX config, `cd` into dotfiles repo, copy the ShareX folder into `src` folder. Example:

```sh
$ cp -r /mnt/c/Users/erwin.gaitan/ShareX src
```

## Notes

On 2021/08/17, Mac Big Sur 11.5.1, I had issues with the Karabiner-Elements (13.5.0) driver
which didn't want to work activate properly. After many tries, I was able to make
it work by going into "Security & Privacy" and clicking "Allow". At first, the "Allow"
button was not appearing and I tried everything, the thing I think it worked was to
create a file in `~/Library/LaunchAgents/com.local.KeyRemapping.plist`. Also, I started to
download a MacOs update (it was in progress in the moment the "Allow" button appeared)

## TODO:

- [ ] Test 4 failing for KeyRemapper