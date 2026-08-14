#MenuTitle: Vertical Metrics Creator
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__="""
Measures the glyphs and the master metrics of the font, calculates typo, hhea and win vertical metrics out of them, and writes them as custom parameters into every master. Same values in all masters, so line spacing stays consistent across the family. Runs automatically with the last used settings; hold down OPTION while starting the script to open the dialog instead.
"""

from GlyphsApp import *
from AppKit import NSEvent

prefID = "com.rsztype.VerticalMetricsCreator"

parameterNames = (
	"typoAscender", "typoDescender", "typoLineGap",
	"winAscent", "winDescent",
	"hheaAscender", "hheaDescender", "hheaLineGap",
)

basisOptions = (
	"measured glyph extremes",
	"master ascender and descender",
	"extremes for win, design for typo",
)

def domain( prefName ):
	return "%s.%s" % (prefID, prefName.strip())

def pref( prefName ):
	return Glyphs.defaults[ domain(prefName) ]

def registerDefaults():
	Glyphs.registerDefault( domain("basis"), 0 )
	Glyphs.registerDefault( domain("roundBy"), "10" )
	Glyphs.registerDefault( domain("ignoreMarks"), 0 )
	Glyphs.registerDefault( domain("useTypoMetrics"), 1 )

def optionKeyPressed():
	NSAlternateKeyMask = 524288 # 1 << 19
	return NSEvent.modifierFlags() & NSAlternateKeyMask == NSAlternateKeyMask

def roundUpByValue( value, roundBy ):
	"""Rounds away from zero, e.g. 3893 → 3900 and -1093 → -1100 with roundBy=10."""
	if not roundBy or value == 0:
		return int(value)
	sign = -1 if value < 0 else 1
	absoluteValue = abs(value)
	roundedValue = absoluteValue // roundBy * roundBy
	if absoluteValue % roundBy:
		roundedValue += roundBy
	return int(roundedValue * sign)

def measureFont( thisFont, ignoreMarks=False ):
	"""Returns (highestPoint, lowestPoint, highestGlyphName, lowestGlyphName) over all masters."""
	highest, lowest = None, None
	highestGlyphName, lowestGlyphName = "", ""
	for thisMaster in thisFont.masters:
		for thisGlyph in thisFont.glyphs:
			if not thisGlyph.export:
				continue
			if ignoreMarks and thisGlyph.subCategory == "Nonspacing":
				continue
			thisLayer = thisGlyph.layers[thisMaster.id]
			if not thisLayer or (not thisLayer.paths and not thisLayer.components):
				continue
			bounds = thisLayer.bounds
			topOfLayer = bounds.origin.y + bounds.size.height
			bottomOfLayer = bounds.origin.y
			if highest is None or topOfLayer > highest:
				highest = topOfLayer
				highestGlyphName = "%s (%s)" % (thisGlyph.name, thisMaster.name)
			if lowest is None or bottomOfLayer < lowest:
				lowest = bottomOfLayer
				lowestGlyphName = "%s (%s)" % (thisGlyph.name, thisMaster.name)
	if highest is None:
		return 0, 0, "", ""
	return highest, lowest, highestGlyphName, lowestGlyphName

def calculateMetrics( thisFont, basis=0, roundBy=10, ignoreMarks=False, measurement=None ):
	"""Returns a dict with the eight values, plus the names of the extreme glyphs."""
	if measurement is None:
		measurement = measureFont( thisFont, ignoreMarks )
	highest, lowest, highestGlyphName, lowestGlyphName = measurement

	measuredAscender = roundUpByValue( highest, roundBy )
	measuredDescender = roundUpByValue( lowest, roundBy ) # negative
	designAscender = roundUpByValue( max([m.ascender for m in thisFont.masters]), roundBy )
	designDescender = roundUpByValue( min([m.descender for m in thisFont.masters]), roundBy ) # negative

	if basis == 1:
		# master ascender and descender, win widened if glyphs stick out
		metrics = {
			"typoAscender": designAscender, "typoDescender": designDescender, "typoLineGap": 0,
			"hheaAscender": designAscender, "hheaDescender": designDescender, "hheaLineGap": 0,
			"winAscent": max(measuredAscender, designAscender),
			"winDescent": abs(min(measuredDescender, designDescender)),
		}
	elif basis == 2:
		# win and hhea from the extremes, typo from the design metrics
		metrics = {
			"typoAscender": designAscender, "typoDescender": designDescender, "typoLineGap": 0,
			"hheaAscender": measuredAscender, "hheaDescender": measuredDescender, "hheaLineGap": 0,
			"winAscent": measuredAscender, "winDescent": abs(measuredDescender),
		}
	else:
		# measured glyph extremes for everything
		metrics = {
			"typoAscender": measuredAscender, "typoDescender": measuredDescender, "typoLineGap": 0,
			"hheaAscender": measuredAscender, "hheaDescender": measuredDescender, "hheaLineGap": 0,
			"winAscent": measuredAscender, "winDescent": abs(measuredDescender),
		}

	metrics["highest"] = highest
	metrics["lowest"] = lowest
	metrics["highestGlyphName"] = highestGlyphName
	metrics["lowestGlyphName"] = lowestGlyphName
	return metrics

def applyMetrics( thisFont, values, useTypoMetrics=True ):
	"""Writes the eight parameters into every master. Returns the number of written parameters."""
	typoLineHeight = values["typoAscender"] - values["typoDescender"] + values["typoLineGap"]
	winLineHeight = values["winAscent"] + values["winDescent"]
	if winLineHeight < typoLineHeight:
		print("⚠️ win line height (%i) is smaller than typo line height (%i). Glyphs may be clipped in Windows apps." % (winLineHeight, typoLineHeight))
		print()

	writtenParameterCount = 0
	for thisMaster in thisFont.masters:
		print("Master %s:" % thisMaster.name)
		for parameterName in parameterNames:
			newValue = values[parameterName]
			oldValue = thisMaster.customParameters[parameterName]
			try:
				oldValueAsNumber = int(oldValue)
			except:
				oldValueAsNumber = None
			thisMaster.customParameters[parameterName] = newValue
			writtenParameterCount += 1
			if oldValue is None:
				print("  ✅ %s = %i" % (parameterName, newValue))
			elif oldValueAsNumber != newValue:
				print("  ♻️ %s = %i (was: %s)" % (parameterName, newValue, oldValue))
			else:
				print("  ☑️ %s = %i (unchanged)" % (parameterName, newValue))
		print()

	if useTypoMetrics:
		thisFont.customParameters["Use Typo Metrics"] = True
		print("✅ Font: Use Typo Metrics = yes")
		print()

	return writtenParameterCount

def reportHeader( thisFont ):
	print("Vertical Metrics Creator Report for %s" % thisFont.familyName)
	if thisFont.filepath:
		print(thisFont.filepath)
	else:
		print("⚠️ The font file has not been saved yet.")
	print()

def runAutomatically():
	"""Measures, calculates and applies in one go, with the settings last used in the dialog."""
	Glyphs.clearLog()
	thisFont = Glyphs.font
	if not thisFont:
		Message( title="No Font Open", message="The script requires a font. Open a font and run the script again.", OKButton=None )
		return

	try:
		roundBy = int( pref("roundBy") )
	except:
		roundBy = 10
	basis = int( pref("basis") or 0 )
	ignoreMarks = bool( pref("ignoreMarks") )
	useTypoMetrics = bool( pref("useTypoMetrics") )

	reportHeader( thisFont )
	print("Settings: %s, rounded up to %i, %s marks. Hold down OPTION while starting the script to change them." % (
		basisOptions[basis],
		roundBy,
		"ignoring" if ignoreMarks else "including",
	))

	metrics = calculateMetrics( thisFont, basis=basis, roundBy=roundBy, ignoreMarks=ignoreMarks )
	print("Highest: %s at %i · Lowest: %s at %i" % (
		metrics["highestGlyphName"] if metrics["highestGlyphName"] else "–", metrics["highest"],
		metrics["lowestGlyphName"] if metrics["lowestGlyphName"] else "–", metrics["lowest"],
	))
	print()

	writtenParameterCount = applyMetrics( thisFont, metrics, useTypoMetrics )

	Glyphs.showNotification(
		"%s: vertical metrics set" % thisFont.familyName,
		"typo/hhea %i/%i, win %i/%i in %i master%s. Details in Macro Window." % (
			metrics["typoAscender"], metrics["typoDescender"],
			metrics["winAscent"], metrics["winDescent"],
			len(thisFont.masters),
			"" if len(thisFont.masters)==1 else "s",
		),
	)
	print("Done. Wrote %i parameters." % writtenParameterCount)

class VerticalMetricsCreator( object ):
	def __init__( self ):
		import vanilla
		self.vanilla = vanilla

		# Window 'self.w':
		windowWidth  = 350
		windowHeight = 290
		windowWidthResize  = 100 # user can resize width by this value
		windowHeightResize = 0   # user can resize height by this value
		self.w = vanilla.FloatingWindow(
			( windowWidth, windowHeight ), # default window size
			"Vertical Metrics Creator", # window title
			minSize = ( windowWidth, windowHeight ), # minimum size (for resizing)
			maxSize = ( windowWidth + windowWidthResize, windowHeight + windowHeightResize ), # maximum size (for resizing)
			autosaveName = "%s.mainwindow" % prefID # stores last window position and size
		)

		# UI elements:
		linePos, inset, lineHeight = 12, 15, 22
		column, columnWidth = inset+95, 62

		self.w.descriptionText = vanilla.TextBox( (inset, linePos+2, -inset, 14), "Calculate vertical metrics and put them in all masters:", sizeStyle='small', selectable=True )
		linePos += lineHeight

		self.w.titleAscender = vanilla.TextBox( (column+columnWidth*0, linePos+2, columnWidth, 14), "Ascender", sizeStyle='small', selectable=True )
		self.w.titleDescender = vanilla.TextBox( (column+columnWidth*1, linePos+2, columnWidth, 14), "Descender", sizeStyle='small', selectable=True )
		self.w.titleLineGap = vanilla.TextBox( (column+columnWidth*2, linePos+2, columnWidth, 14), "Line Gap", sizeStyle='small', selectable=True )
		linePos += lineHeight - 4

		self.w.titleTypo = vanilla.TextBox( (inset, linePos+3, 95, 14), "OS/2 sTypo*", sizeStyle='small', selectable=True )
		self.w.typoAscender = vanilla.EditText( (column+columnWidth*0, linePos, columnWidth-6, 19), "", callback=self.SavePreferences, sizeStyle='small' )
		self.w.typoDescender = vanilla.EditText( (column+columnWidth*1, linePos, columnWidth-6, 19), "", callback=self.SavePreferences, sizeStyle='small' )
		self.w.typoLineGap = vanilla.EditText( (column+columnWidth*2, linePos, columnWidth-6, 19), "", callback=self.SavePreferences, sizeStyle='small' )
		linePos += lineHeight

		self.w.titleHhea = vanilla.TextBox( (inset, linePos+3, 95, 14), "hhea", sizeStyle='small', selectable=True )
		self.w.hheaAscender = vanilla.EditText( (column+columnWidth*0, linePos, columnWidth-6, 19), "", callback=self.SavePreferences, sizeStyle='small' )
		self.w.hheaDescender = vanilla.EditText( (column+columnWidth*1, linePos, columnWidth-6, 19), "", callback=self.SavePreferences, sizeStyle='small' )
		self.w.hheaLineGap = vanilla.EditText( (column+columnWidth*2, linePos, columnWidth-6, 19), "", callback=self.SavePreferences, sizeStyle='small' )
		linePos += lineHeight

		self.w.titleWin = vanilla.TextBox( (inset, linePos+3, 95, 14), "OS/2 usWin", sizeStyle='small', selectable=True )
		self.w.winAscent = vanilla.EditText( (column+columnWidth*0, linePos, columnWidth-6, 19), "", callback=self.SavePreferences, sizeStyle='small' )
		self.w.winDescent = vanilla.EditText( (column+columnWidth*1, linePos, columnWidth-6, 19), "", callback=self.SavePreferences, sizeStyle='small' )
		self.w.winNote = vanilla.TextBox( (column+columnWidth*2, linePos+3, columnWidth, 14), "(positive)", sizeStyle='small', selectable=True )
		linePos += lineHeight + 4

		self.w.basisText = vanilla.TextBox( (inset, linePos+3, 60, 14), "Based on", sizeStyle='small', selectable=True )
		self.w.basis = vanilla.PopUpButton( (inset+60, linePos+1, -inset, 17), basisOptions, sizeStyle='small', callback=self.measureAndUpdate )
		self.w.basis.getNSPopUpButton().setToolTip_(
			"Measured glyph extremes: the highest and lowest points of all exporting glyphs, in all masters.\n"
			"Master ascender and descender: the values from Font Info > Masters.\n"
			"Mixed: win and hhea from the extremes (avoids clipping), typo from the design metrics."
		)
		linePos += lineHeight

		self.w.roundText = vanilla.TextBox( (inset, linePos+3, 60, 14), "Round up to", sizeStyle='small', selectable=True )
		self.w.roundBy = vanilla.EditText( (inset+75, linePos, 45, 19), "10", callback=self.measureAndUpdate, sizeStyle='small' )
		self.w.roundBy.getNSTextField().setToolTip_("Rounds the measured values up to a multiple of this number. Set to 1 or 0 for no rounding.")
		self.w.ignoreMarks = vanilla.CheckBox( (inset+135, linePos, -inset, 20), "Ignore non-spacing marks", value=False, callback=self.measureAndUpdate, sizeStyle='small' )
		self.w.ignoreMarks.getNSButton().setToolTip_("If enabled, does not measure combining accents. Careful: tall marks can be clipped in some apps if win is too small.")
		linePos += lineHeight

		self.w.useTypoMetrics = vanilla.CheckBox( (inset, linePos, -inset, 20), "Also set ‘Use Typo Metrics’ in Font Info > Font", value=True, callback=self.SavePreferences, sizeStyle='small' )
		self.w.useTypoMetrics.getNSButton().setToolTip_("Strongly recommended: makes apps use the typo values for line spacing, which is what keeps the family consistent.")
		linePos += lineHeight

		self.w.statusText = vanilla.TextBox( (inset, -30-inset, -190-inset, 30), "", sizeStyle='small', selectable=True )

		# Buttons:
		self.w.measureButton = vanilla.Button( (-180-inset, -20-inset, -90-inset, -inset), "Measure", sizeStyle='regular', callback=self.measureAndUpdate )
		self.w.runButton = vanilla.Button( (-80-inset, -20-inset, -inset, -inset), "Apply", sizeStyle='regular', callback=self.VerticalMetricsCreatorMain )
		self.w.setDefaultButton( self.w.runButton )

		# Load Settings:
		if not self.LoadPreferences():
			print("Note: 'Vertical Metrics Creator' could not load preferences. Will resort to defaults")

		# Open window and focus on it:
		self.measureAndUpdate()
		self.w.open()
		self.w.makeKey()

	def intValue( self, editField ):
		try:
			return int(round(float( editField.get().strip().replace(",", ".") )))
		except:
			return 0

	def cachedMeasurement( self, thisFont, ignoreMarks ):
		"""Keeps the last scan, so that typing in the rounding field does not rescan the whole font."""
		cacheKey = ( thisFont.familyName, len(thisFont.glyphs), len(thisFont.masters), bool(ignoreMarks) )
		if getattr(self, "measurementCacheKey", None) != cacheKey:
			self.measurementCacheKey = cacheKey
			self.measurementCache = measureFont( thisFont, ignoreMarks )
		return self.measurementCache

	def measureAndUpdate( self, sender=None ):
		if sender is not None and sender == getattr( self.w, "measureButton", None ):
			# the button always forces a fresh scan:
			self.measurementCacheKey = None

		thisFont = Glyphs.font
		if not thisFont:
			self.w.statusText.set("⚠️ No font open.")
			self.w.runButton.enable(False)
			return

		try:
			roundBy = int( self.w.roundBy.get().strip() )
		except:
			roundBy = 0
		ignoreMarks = bool( self.w.ignoreMarks.get() )

		metrics = calculateMetrics(
			thisFont,
			basis = self.w.basis.get(),
			roundBy = roundBy,
			ignoreMarks = ignoreMarks,
			measurement = self.cachedMeasurement( thisFont, ignoreMarks ),
		)
		for parameterName in parameterNames:
			getattr( self.w, parameterName ).set( str(metrics[parameterName]) )
		self.w.statusText.set( "Highest: %s\nLowest: %s" % (
			metrics["highestGlyphName"] if metrics["highestGlyphName"] else "–",
			metrics["lowestGlyphName"] if metrics["lowestGlyphName"] else "–",
		) )
		self.SavePreferences()

	def updateUI( self, sender=None ):
		self.w.runButton.enable( Glyphs.font is not None )

	def SavePreferences( self, sender=None ):
		try:
			Glyphs.defaults[ domain("basis") ] = self.w.basis.get()
			Glyphs.defaults[ domain("roundBy") ] = self.w.roundBy.get()
			Glyphs.defaults[ domain("ignoreMarks") ] = self.w.ignoreMarks.get()
			Glyphs.defaults[ domain("useTypoMetrics") ] = self.w.useTypoMetrics.get()
			self.updateUI()
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	def LoadPreferences( self ):
		try:
			registerDefaults()
			self.w.basis.set( pref("basis") )
			self.w.roundBy.set( pref("roundBy") )
			self.w.ignoreMarks.set( pref("ignoreMarks") )
			self.w.useTypoMetrics.set( pref("useTypoMetrics") )
			self.updateUI()
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	def VerticalMetricsCreatorMain( self, sender=None ):
		try:
			# clear macro window log:
			Glyphs.clearLog()

			if not self.SavePreferences():
				print("Note: 'Vertical Metrics Creator' could not write preferences.")

			thisFont = Glyphs.font
			if not thisFont:
				Message( title="No Font Open", message="The script requires a font. Open a font and run the script again.", OKButton=None )
				return

			reportHeader( thisFont )

			# take the values from the fields, so manual corrections are respected:
			values = {}
			for parameterName in parameterNames:
				values[parameterName] = self.intValue( getattr(self.w, parameterName) )

			if values["winAscent"] < 0 or values["winDescent"] < 0:
				Message(
					title="Negative win Values",
					message="winAscent and winDescent must be positive numbers. Fix the values and try again.",
					OKButton=None,
				)
				return

			writtenParameterCount = applyMetrics( thisFont, values, self.w.useTypoMetrics.get() )

			self.w.close() # delete if you want window to stay open

			# Final report:
			Glyphs.showNotification(
				"%s: vertical metrics set" % thisFont.familyName,
				"typo/hhea %i/%i, win %i/%i in %i master%s. Details in Macro Window." % (
					values["typoAscender"], values["typoDescender"],
					values["winAscent"], values["winDescent"],
					len(thisFont.masters),
					"" if len(thisFont.masters)==1 else "s",
				),
			)
			print("Done. Wrote %i parameters." % writtenParameterCount)

		except Exception as e:
			# brings macro window to front and reports error:
			Glyphs.showMacroWindow()
			print("Vertical Metrics Creator Error: %s" % e)
			import traceback
			print(traceback.format_exc())

registerDefaults()
if optionKeyPressed():
	# OPTION key held down: let the user check and adjust the values first
	VerticalMetricsCreator()
else:
	# default: measure, calculate and apply in one go
	runAutomatically()
