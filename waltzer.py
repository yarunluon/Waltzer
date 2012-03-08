#!/usr/bin/env python
# encoding: utf=8

"""
waltzer.py

Convert your song into a waltz. Only works for songs in 4/4 time
Created by Yarun Luon
Code based on swinger.py by Tristan Jehan which can be found here:
http://code.google.com/p/echo-nest-remix/source/browse/trunk/examples/swinger/swinger.py

MIT License
"""

from optparse import OptionParser
import os, sys
import dirac

from echonest.audio import LocalAudioFile, AudioData
from echonest.action import render, Playback, display_actions

def do_work(track, options):

	verbose = bool(options.verbose)

	if track.analysis.time_signature['value'] in [3,6]:
		if verbose: print "Song is already a waltz"
		return Playback(track, 0, track.analysis.duration)
	
	# Figure out what to do with the bastard beat
	bastard = int(options.waltz)
	if bastard < 1: bastard = 2
	if bastard > 3: bastard = 2
	
	beats = track.analysis.beats
	offset = int(beats[0].start * track.sampleRate)

	rates = []

	# Set offset according to bastard beat
	count = (2,1,4)[bastard - 1] 

	if verbose:
		print "Putting extra beat on beat %s" % bastard
	
	# Convert a song in 4/4 to 3/4
	for beat in beats:
		if count in [1, 4]: 
			rate = 4.0/3.0
		if count in [2, 3]: 
			rate = 2.0/3.0
		
		if count == 4:
			count = 1
		else:
			count += 1
		
		start = int(beat.start * track.sampleRate)
		rates.append((start-offset, rate))
		
	# get audio
	vecin = track.data[offset:int(beats[-1].start * track.sampleRate),:]
	# time stretch
	if verbose: 
		print "\nTime stretching..."
	vecout = dirac.timeScale(vecin, rates, track.sampleRate, 0)
	# build timestretch AudioData object
	ts = AudioData(ndarray=vecout, shape=vecout.shape, 
					sampleRate=track.sampleRate, numChannels=vecout.shape[1], 
					verbose=verbose)
	
	# initial and final playback
	pb1 = Playback(track, 0, beats[0].start)
	pb2 = Playback(track, beats[-1].start, track.analysis.duration-beats[-1].start)

	return [pb1, ts, pb2]

def main():
	usage = "usage: %s [options] <one_single_mp3>" % sys.argv[0]
	parser = OptionParser(usage=usage)
	parser.add_option("-w", "--waltz", default=2, help="where to put the extra beat, value of 1, 2, or 3, default=2")
	parser.add_option("-v", "--verbose", action="store_true", help="show results on screen")
	
	(options, args) = parser.parse_args()
	if len(args) < 1:
		parser.print_help()
		return -1
	
	verbose = options.verbose
	track = None
	
	track = LocalAudioFile(args[0], verbose=verbose)
	if verbose:
		print "Computing waltz . . ."
		
	# this is where the work takes place
	actions = do_work(track, options)

	if verbose:
		display_actions(actions)

	if verbose:
		print "Song is in %s/4 time" % int(track.analysis.time_signature['value'])
	
	# Send to renderer
	name = os.path.splitext(os.path.basename(args[0]))

	name = name[0] + '_waltz_b' + str(int(options.waltz)) + '.mp3'
	name = name.replace(' ','') 
	name = os.path.join(os.getcwd(), name) # TODO: use sys.path[0] instead of getcwd()?

	if verbose:
		print "Rendering... %s" % name
        
	render(actions, name, verbose=verbose)
	if verbose:
		print "Success!"
	return 1


if __name__ == "__main__":
	try:
		main()
	except Exception, e:
		print e
