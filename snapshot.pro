;Function modified from http://www.idlcoyote.com/programs/cgsnapshot.pro
FUNCTION snapshot, filename, xstart=xstart, ystart=ystart, ncols=ncols, nrows=nrows, $
   Colors=colors, $
   Order=order, $
   POSITION=position, $
   True=true, $
   WID=wid, $
   _Ref_Extra=extra
   

   ; Error handling.
   Catch, theError
   IF theError NE 0 THEN BEGIN
       Catch, /Cancel
       print,"SNAPSHOT ERROR: ",theError
       IF N_Elements(thisWindow) EQ 0 THEN RETURN, -1
       IF thisWindow GE 0 THEN WSet, thisWindow
       
       ; Need to set color decomposition back?
       IF (N_Elements(theDecomposedState) NE 0) && (theDepth GT 0) THEN BEGIN
           Device, Decomposed=theDecomposedState
       ENDIF
       RETURN, -1
    ENDIF
    
    ; Go to correct window.
    IF not keyword_set(wid) THEN wid =!D.Window
    thisWindow = !D.Window
    IF (!D.Flags AND 256) NE 0 THEN WSet, wid
    
    ; Did the user specify a normalized position in the window?
    IF keyword_set(position) THEN BEGIN
       xstart = position[0] * !D.X_VSize
       ystart = position[1] * !D.Y_VSize
       ncols = (position[2]*!D.X_VSize) - xstart
       nrows = (position[3]*!D.Y_VSize) - ystart
    ENDIF
    
    ; Check keywords and parameters. Define values if necessary.
    IF not keyword_set(xstart) THEN xstart = 0
    IF not keyword_set(ystart) THEN ystart = 0
    IF not keyword_set(ncols) THEN ncols = !D.X_VSize - xstart
    IF not keyword_set(nrows) THEN nrows = !D.Y_VSize - ystart
    IF not keyword_set(order) THEN order = !Order
    IF not keyword_set(true) THEN true = 1
    
    IF N_Elements(colors) EQ 0 THEN colors = 256

    ; On 24-bit displays, make sure color decomposition is ON.
    IF (!D.Flags AND 256) NE 0 THEN BEGIN
       Device, Get_Decomposed=theDecomposedState, Get_Visual_Depth=theDepth
       IF theDepth GT 8 THEN BEGIN
          Device, Decomposed=1
          IF theDepth EQ 24 THEN truecolor = true ELSE truecolor = 0
       ENDIF ELSE truecolor = 0
       IF wid LT 0 THEN BEGIN
          Message, 'No currently open windows. Returning.', /NoName
          return, -1
       ENDIF
    ENDIF ELSE BEGIN
       truecolor = 0
       theDepth = 8
    ENDELSE
    
    ; Fix for 24-bit Z-buffer.
    IF (Float(!Version.Release) GE 6.4) AND (!D.NAME EQ 'Z') THEN BEGIN
       Device, Get_Decomposed=theDecomposedState, Get_Pixel_Depth=theDepth
       IF theDepth EQ 24 THEN truecolor = true ELSE truecolor = 0
    ENDIF
    
    ; Get the screen dump. 2D image on 8-bit displays. 3D image on 24-bit displays.
    image = TVRD(xstart,ystart,ncols,nrows,True=truecolor, Order=order)
    
    ; Need to set color decomposition back?
    IF theDepth GT 8 THEN Device, Decomposed=theDecomposedState
    
    IF truecolor THEN BEGIN
        Write_PNG, filename, image, _Extra=extra
    ENDIF ELSE BEGIN
        TVLCT, r, g, b, /Get
        image2D = image
        Write_PNG, filename, image2D, r, g, b, _Extra=extra
    ENDELSE
    
END
