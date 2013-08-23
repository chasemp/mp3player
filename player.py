#based on http://www.blog.pythonlibrary.org/2010/04/20/wxpython-creating-a-simple-mp3-player/
import os
import wx
import wx.media
import wx.lib.buttons as buttons
#for mp3 meta info grabbing
from meta import listDirectory
from meta import MP3FileInfo
import os.path

dirName = os.path.dirname(os.path.abspath(__file__))
bitmapDir = os.path.join(dirName, 'bitmaps')

########################################################################
class MediaPanel(wx.Panel):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        
        self.frame = parent
        self.currentVolume = 50
        self.createMenu()
        self.layoutControls()
        
        sp = wx.StandardPaths.Get()
        self.currentFolder = sp.GetDocumentsDir()
        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer)
        self.timer.Start(100)
        self.list_place = 0
        self.musicList = []

    #----------------------------------------------------------------------
    def layoutControls(self):
        """
        Create and layout the widgets
        """
        
        try:
            self.mediaPlayer = wx.media.MediaCtrl(self, style=wx.SIMPLE_BORDER)
        except NotImplementedError:
            self.Destroy()
            raise
                
        # create playback slider
        self.playbackSlider = wx.Slider(self, size=wx.DefaultSize)
        self.Bind(wx.EVT_SLIDER, self.onSeek, self.playbackSlider)
        
        #self.volumeCtrl = wx.Slider(self, style=wx.SL_VERTICAL|wx.SL_INVERSE)
        self.volumeCtrl = wx.Slider(self, style=wx.HORIZONTAL)
        self.volumeCtrl.SetRange(0, 100)
        self.volumeCtrl.SetValue(self.currentVolume)
        self.volumeCtrl.Bind(wx.EVT_SLIDER, self.onSetVolume)
      

        # Create sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        audioSizer = self.buildAudioBar()
                
        #ATTEMPT AT SONGTITLE DISPLAY
        self.now_playing = wx.StaticText(self, wx.ID_ANY, 'Now Playing:', (20, 100))
        tSizer = wx.BoxSizer(wx.HORIZONTAL)
        tSizer.Add(self.now_playing, 0, wx.ALL|wx.CENTER, 5)
        mainSizer.Add(tSizer)

        #ATTEMPT AT SONGTITLE DISPLAY
        self.songTitle = wx.StaticText(self, wx.ID_ANY, label="Song Title", style=wx.ALIGN_CENTRE)
        sSizer = wx.BoxSizer(wx.HORIZONTAL)
        sSizer.Add(self.songTitle, 0, wx.ALL|wx.RIGHT, 5)
        mainSizer.Add(sSizer)

        # layout widgets
        mainSizer.Add(self.playbackSlider, 1, wx.ALL|wx.EXPAND, 5)
        hSizer.Add(audioSizer, 0, wx.ALL|wx.CENTER, 5)
        hSizer.Add(self.volumeCtrl, 0, wx.ALL|wx.CENTER, 5)
        mainSizer.Add(hSizer)
        
        self.SetSizer(mainSizer)
        self.Layout()
        
    #----------------------------------------------------------------------
    def buildAudioBar(self):
        """
        Builds the audio bar controls
        """
        audioBarSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.buildBtn({'bitmap':'player_prev.png', 'handler':self.onPrev,
                       'name':'prev'},
                      audioBarSizer)
        
        # create play/pause toggle button
        img = wx.Bitmap(os.path.join(bitmapDir, "player_play.png"))
        self.playPauseBtn = buttons.GenBitmapToggleButton(self, bitmap=img, name="play")
        self.playPauseBtn.Enable(False)
        
        img = wx.Bitmap(os.path.join(bitmapDir, "player_pause.png"))
        self.playPauseBtn.SetBitmapSelected(img)
        self.playPauseBtn.SetInitialSize()
        
        self.playPauseBtn.Bind(wx.EVT_BUTTON, self.onPlay)
        audioBarSizer.Add(self.playPauseBtn, 0, wx.LEFT, 3)
        
        btnData = [{'bitmap':'player_stop.png',
                    'handler':self.onStop, 'name':'stop'},
                    {'bitmap':'player_next.png',
                     'handler':self.onNext, 'name':'next'}]
        for btn in btnData:
            self.buildBtn(btn, audioBarSizer)
            
        return audioBarSizer
                    
    #----------------------------------------------------------------------
    def buildBtn(self, btnDict, sizer):
        """"""
        bmp = btnDict['bitmap']
        handler = btnDict['handler']
                
        img = wx.Bitmap(os.path.join(bitmapDir, bmp))
        btn = buttons.GenBitmapButton(self, bitmap=img, name=btnDict['name'])
        btn.SetInitialSize()
        btn.Bind(wx.EVT_BUTTON, handler)
        sizer.Add(btn, 0, wx.LEFT, 3)
        
    #----------------------------------------------------------------------
    def createMenu(self):
        """
        Creates a menu
        """
        menubar = wx.MenuBar()
        
        fileMenu = wx.Menu()

        open_file_menu_item = fileMenu.Append(wx.NewId(), "&Open", "Open a file")
        add_file_menu_item = fileMenu.Append(wx.NewId(), "&Add", "Add files")

        menubar.Append(fileMenu, '&File')

        self.frame.SetMenuBar(menubar)

        self.frame.Bind(wx.EVT_MENU, self.onBrowse, open_file_menu_item)

        self.frame.Bind(wx.EVT_MENU, self.onBrowseAdd, add_file_menu_item)

    def createStatusBar(self):
        """
        NOT IMPLEMENTED
        Creates a status bar
        """
        statusbar = wx.StatusBar()
        
        fileMenu = wx.Menu()
        open_file_menu_item = fileMenu.Append(wx.NewId(), "&Open", "Open a file")
        add_file_menu_item = fileMenu.Append(wx.NewId(), "&Add", "Add files")

        menubar.Append(fileMenu, '&File')
        self.frame.SetMenuBar(menubar)
        self.frame.Bind(wx.EVT_MENU, self.onBrowse, open_file_menu_item)

        self.frame.Bind(wx.EVT_MENU, self.onBrowseAdd, add_file_menu_item)
        
    #----------------------------------------------------------------------
    def loadMusic(self, musicFile):
        """"""
        if not self.mediaPlayer.Load(musicFile):
            wx.MessageBox("Unable to load %s: Unsupported format?" % path,
                          "ERROR",
                          wx.ICON_ERROR | wx.OK)
        else:
            self.mediaPlayer.SetInitialSize()
            self.GetSizer().Layout()
            self.playbackSlider.SetRange(0, self.mediaPlayer.Length())
            self.playPauseBtn.Enable(True)

        metatag = MP3FileInfo(musicFile)

        if 'artist' in metatag:
            if 'title' in metatag:
                songinfo = "%s - %s" % (metatag['artist'], metatag['title'])

        if 'artist' not in metatag:
            metatag['artist'] = "!ID3"

        if 'title' not in metatag:
	    title = os.path.basename(musicFile.strip(".mp3"))
            metatag['title'] = title
            songinfo = "%s" % (metatag['title'])




        self.songTitle.SetLabel(songinfo)
        self.Play()

        print musicFile

    #----------------------------------------------------------------------
    def onBrowseAdd(self, event, append=False):
        """
        Opens file dialog to browse for music
        """
        if append:
            print "I should append"

        wildcard = "MP3 (*.mp3)|*.mp3|"     \
                   "WAV (*.wav)|*.wav"
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=self.currentFolder, 
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPaths()
            print "path: " + str(path)
            self.currentFolder = os.path.dirname(path[0])
            
            if self.list_place != 0:
                self.list_place += 1

            for song in path:
                print "Adding: " + song
                self.musicList.append(song)

            #self.allPlay(self.musicList)
            self.loadMusic(self.musicList[self.list_place])

        dlg.Destroy()
    #----------------------------------------------------------------------
    def onBrowse(self, event, append=False):
        """
        Opens file dialog to browse for music
        """
        if append:
            print "I should append"

        wildcard = "MP3 (*.mp3)|*.mp3|"     \
                   "WAV (*.wav)|*.wav"
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=self.currentFolder, 
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
            )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPaths()
            print "path: " + str(path)
            self.currentFolder = os.path.dirname(path[0])
            
            self.musicList = path

            for song in self.musicList:
                print "Music: " + song

            self.loadMusic(path[self.list_place])

        dlg.Destroy()
            
    #----------------------------------------------------------------------

    def Next(self):

        if len(self.musicList) < self.list_place + 2:
            self.list_place = 0
        else:
            self.list_place += 1

        print "Place: " + str(self.list_place)

        self.loadMusic(self.musicList[self.list_place])
        print "Loading: " + self.musicList[self.list_place] 

        self.Play()
        pass

    def onNext(self, event):

        if not event.GetIsDown():
            self.onPause()
            return

        self.Next()

    
    #----------------------------------------------------------------------
    def onPause(self):
        """
        Pauses the music
        """
        self.mediaPlayer.Pause()

    #----------------------------------------------------------------------
    def Play(self):
        """
        Play the music
        """

        if not self.mediaPlayer.Play():
            wx.MessageBox("Unable to Play media : Unsupported format?",
                          "ERROR",
                          wx.ICON_ERROR | wx.OK)
        else:
            self.mediaPlayer.SetInitialSize()
            self.GetSizer().Layout()
            self.playbackSlider.SetRange(0, self.mediaPlayer.Length())




    #----------------------------------------------------------------------
    def onPlay(self, event):
        """
        Plays the music
        """
        if not event.GetIsDown():
            self.onPause()
            return
        
        self.Play()
       
        event.Skip()
    
    #----------------------------------------------------------------------
    def allPlay(self, songList):
        """
        Play the music
        """
        for song in songList:
            print "Loading: " + self.musicList[self.list_place] 
            self.loadMusic(songList[self.list_place])
            self.list_place += 1
            self.Play()


    #----------------------------------------------------------------------
    def onPrev(self, event):
        """
        """
        if self.list_place == 0:
            self.list_place = len(self.musicList) - 2
        else:
            self.list_place -= 1

        print "Place: " + str(self.list_place)

        self.loadMusic(self.musicList[self.list_place])
        print "Loading: " + self.musicList[self.list_place] 

        if not event.GetIsDown():
            self.onPause()
            return

        self.Play()
        pass
    
    #----------------------------------------------------------------------
    def onSeek(self, event):
        """
        Seeks the media file according to the amount the slider has
        been adjusted.
        """
        offset = self.playbackSlider.GetValue()
        self.mediaPlayer.Seek(offset)
        
    #----------------------------------------------------------------------
    def onSetVolume(self, event):
        """
        Sets the volume of the music player
        """
        self.currentVolume = self.volumeCtrl.GetValue()
        print "setting volume to: %s" % int(self.currentVolume)
        self.mediaPlayer.SetVolume(float(self.currentVolume) / 100)    


    #----------------------------------------------------------------------
    def onStop(self, event):
        """
        Stops the music and resets the play button
        """
        self.mediaPlayer.Stop()
        self.playPauseBtn.SetToggle(False)
        
    #----------------------------------------------------------------------
    def onTimer(self, event):
        """
        Controls continous playback and keeps track of slider
        """
        self.offset = self.mediaPlayer.Tell()
        self.playbackSlider.SetValue(self.offset)

 	dtotal = self.mediaPlayer.GetDownloadTotal()
        #print "dtotal " + str(dtotal)

 	length = self.mediaPlayer.Length()
        #print "lenght " + str(length)

        #print "offset: " + str(self.offset)

 	state = self.mediaPlayer.GetState()


 
        #print "state " + str(state)
        if state == 0 and self.musicList:
            self.Next()


########################################################################
class MediaFrame(wx.Frame):
 
    #----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "cAMP Music Player")
        panel = MediaPanel(self)

        
#----------------------------------------------------------------------
# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frame = MediaFrame()
    frame.Show()
    app.MainLoop()
