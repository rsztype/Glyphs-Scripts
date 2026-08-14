#MenuTitle: Vertical Metrics Creator
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__="""
Measures the glyphs and the master metrics of the font, calculates typo, hhea and win vertical metrics out of them, and writes them as custom parameters into every master. Same values in all masters, so line spacing stays consistent across the family.
"""

from GlyphsApp import *
import vanilla

parameterNames = (
	"typoAscender", "typoDescender", "typoLineGap",
	"winAscent", "winDescent",
	"hheaAscender", "hheaDescender", "hheaLineGap",
)

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

class VerticalMetricsCreator( object ):
	prefID = "com.rsztype.VerticalMetricsCreator"

	def __init__( self ):
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
			autosaveName = "%s.mainwindow" % self.prefID # stores last window position and size
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
		self.w.basis = vanilla.PopUpButton( (inset+60, linePos+1, -inset, 17), ("measured glyph extremes", "master ascender and descender", "extremes for win, design for typo"), sizeStyle='small', callback=self.measureAndUpdate )
		self.w.basis.getNSPopUpButton().setToolTip_(
			"Measured glyph extremes: the highest and lowest points of all exporting glyphs, in all masters.\n"
			"Master ascender and descender: the values from Font Info > Masters.\n"
			"Mixed: win from the extremes (avoids clipping), typo from the design metrics, hhea like win."
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

		self.w.statusText = vanilla.TextBox( (inset, -30-inset, -110-inset, 30), "", sizeStyle='small', selectable=True )

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

	def domain( self, prefName ):
		return "%s.%s" % (self.prefID, prefName.strip())

	def pref( self, prefName ):
		return Glyphs.defaults[ self.domain(prefName) ]

	def intValue( self, editField ):
		try:
			return int(round(float( editField.get().strip().replace(",", ".") )))
		except:
			return 0

	def measureFont( self, thisFont, ignoreMarks=False ):
		"""Returns (highestPoint, lowestPoint, highestGlyphName, lowestGlyphName) over all masters.
		Caches the result, so that typing in the rounding field does not rescan the whole font."""
		cacheKey = ( thisFont.familyName, len(thisFont.glyphs), len(thisFont.masters), bool(ignoreMarks) )
		if getattr(self, "measurementCacheKey", None) == cacheKey:
			return self.measurementCache

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
			measurement = (0, 0, "", "")
		else:
			measurement = (highest, lowest, highestGlyphName, lowestGlyphName)
		self.measurementCacheKey = cacheKey
		self.measurementCache = measurement
		return measurement

	def calculatedMetrics( self, thisFont ):
		"""Returns a dict with the eight values, plus the names of the extreme glyphs."""
		try:
			roundBy = int( self.w.roundBy.get().strip() )
		except:
			roundBy = 0
		ignoreMarks = bool( self.w.ignoreMarks.get() )
		basis = self.w.basis.get()

		highest, lowest, highestGlyphName, lowestGlyphName = self.measureFont( thisFont, ignoreMarks )
		measuredAscender = roundUpByValue( highest, roundBy )
		measuredDescender = roundUpByValue( lowest, roundBy ) # negative

		designAscender = roundUpByValue( max([m.ascender for m in thisFont.masters]), roundBy )
		designDescender = roundUpByValue( min([m.descender for m in thisFont.masters]), roundBy ) # negative

		if basis == 1:
			# master ascender and descender for everything
			ascender, descender = designAscender, designDescender
			metrics = {
				"typoAscender": ascender, "typoDescender": descender, "typoLineGap": 0,
				"hheaAscender": ascender, "hheaDescender": descender, "hheaLineGap": 0,
				"winAscent": max(measuredAscender, ascender), "winDescent": abs(min(measuredDescender, descender)),
			}
		elif basis == 2:
			# win from the extremes, typo from the design metrics, hhea like win
			metrics = {
				"typoAscender": designAscender, "typoDescender": designDescender, "typoLineGap": 0,
				"hheaAscender": measuredAscender, "hheaDescender": measuredDescender, "hheaLineGap": 0,
				"winAscent": measuredAscender, "winDescent": abs(measuredDescender),
			}
		else:
			# measured glyph extremes for everything
			ascender, descender = measuredAscender, measuredDescender
			metrics = {
				"typoAscender": ascender, "typoDescender": descender, "typoLineGap": 0,
				"hheaAscender": ascender, "hheaDescender": descender, "hheaLineGap": 0,
				"winAscent": ascender, "winDescent": abs(descender),
			}
		metrics["highestGlyphName"] = highestGlyphName
		metrics["lowestGlyphName"] = lowestGlyphName
		metrics["highest"] = highest
		metrics["lowest"] = lowest
		return metrics

	def measureAndUpdate( self, sender=None ):
		if sender is not None and sender == getattr( self.w, "measureButton", None ):
			# the button always forces a fresh scan:
			self.measurementCacheKey = None
		thisFont = Glyphs.font
		if not thisFont:
			self.w.statusText.set("⚠️ No font open.")
			self.w.runButton.enable(False)
			return
		metrics = self.calculatedMetrics( thisFont )
		for parameterName in parameterNames:
			getattr( self.w, parameterName ).set( str(metrics[parameterName]) )
		self.w.statusText.set( "Highest: %s · Lowest: %s" % (
			metrics["highestGlyphName"] if metrics["highestGlyphName"] else "–",
			metrics["lowestGlyphName"] if metrics["lowestGlyphName"] else "–",
		) )
		self.SavePreferences()

	def updateUI( self, sender=None ):
		self.w.runButton.enable( Glyphs.font is not None )

	def SavePreferences( self, sender=None ):
		try:
			Glyphs.defaults[ self.domain("basis") ] = self.w.basis.get()
			Glyphs.defaults[ self.domain("roundBy") ] = self.w.roundBy.get()
			Glyphs.defaults[ self.domain("ignoreMarks") ] = self.w.ignoreMarks.get()
			Glyphs.defaults[ self.domain("useTypoMetrics") ] = self.w.useTypoMetrics.get()
			self.updateUI()
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	def LoadPreferences( self ):
		try:
			# register defaults:
			Glyphs.registerDefault( self.domain("basis"), 0 )
			Glyphs.registerDefault( self.domain("roundBy"), "10" )
			Glyphs.registerDefault( self.domain("ignoreMarks"), 0 )
			Glyphs.registerDefault( self.domain("useTypoMetrics"), 1 )

			# load previously written prefs:
			self.w.basis.set( self.pref("basis") )
			self.w.roundBy.set( self.pref("roundBy") )
			self.w.ignoreMarks.set( self.pref("ignoreMarks") )
			self.w.useTypoMetrics.set( self.pref("useTypoMetrics") )

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

			print("Vertical Metrics Creator Report for %s" % thisFont.familyName)
			if thisFont.filepath:
				print(thisFont.filepath)
			else:
				print("⚠️ The font file has not been saved yet.")
			print()

			# take the values from the fields, so manual corrections are respected:
			values = {}
			for parameterName in parameterNames:
				values[parameterName] = self.intValue( getattr(self.w, parameterName) )

			# sanity checks:
			if values["winAscent"] < 0 or values["winDescent"] < 0:
				Message(
					title="Negative win Values",
					message="winAscent and winDescent must be positive numbers. Fix the values and try again.",
					OKButton=None,
				)
				return

			typoLineHeight = values["typoAscender"] - values["typoDescender"] + values["typoLineGap"]
			winLineHeight = values["winAscent"] + values["winDescent"]
			if winLineHeight < typoLineHeight:
				print("⚠️ win line height (%i) is smaller than typo line height (%i). Glyphs may be clipped in Windows apps." % (winLineHeight, typoLineHeight))
				print()

			for thisMaster in thisFont.masters:
				print("Master %s:" % thisMaster.name)
				for parameterName in parameterNames:
					newValue = values[parameterName]
					oldValue = thisMaster.customParameters[parameterName]
					thisMaster.customParameters[parameterName] = newValue
					try:
						oldValueAsNumber = int(oldValue)
					except:
						oldValueAsNumber = None
					if oldValue is None:
						print("  ✅ %s = %i" % (parameterName, newValue))
					elif oldValueAsNumber != newValue:
						print("  ♻️ %s = %i (was: %s)" % (parameterName, newValue, oldValue))
					else:
						print("  ☑️ %s = %i (unchanged)" % (parameterName, newValue))
				print()

			if self.w.useTypoMetrics.get():
				thisFont.customParameters["Use Typo Metrics"] = True
				print("✅ Font: Use Typo Metrics = yes")
				print()

			self.w.close() # delete if you want window to stay open

			# Final report:
			Glyphs.showNotification(
				"%s: vertical metrics set" % thisFont.familyName,
				"Wrote %i parameters in %i master%s. Details in Macro Window." % (
					len(parameterNames) * len(thisFont.masters),
					len(thisFont.masters),
					"" if len(thisFont.masters)==1 else "s",
				),
			)
			print("Done.")

		except Exception as e:
			# brings macro window to front and reports error:
			Glyphs.showMacroWindow()
			print("Vertical Metrics Creator Error: %s" % e)
			import traceback
			print(traceback.format_exc())

VerticalMetricsCreator()
