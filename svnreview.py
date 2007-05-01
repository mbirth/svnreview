#!/usr/bin/env python
import os
import curses
import logging

#globals
currentLine = 0
page = 0
err = None

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='/tmp/myapp.log',
                    filemode='w')

def getFileList():
    fileList = []
    for line in os.popen("svn status").read().splitlines():
        status = line[0:7].strip()
        if status == "?":
            # ignore files that aren't in version control
            continue
        file = line[7:].strip()
        fileList.append({"status" : status, "file" : file, "checked" : False})
    return fileList 

#def getFileList():
#     fileList = list()
#     for i in range(0,200):
#         fileList.append({"status": "M", "file":"/cosmo/blah" + str(i), "checked": False})
#     return fileList

#init curses
def initCurses():
    global stdscr 
    global pad
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    pad = curses.newpad(1000, 1000)


#clean up
def cleanupCurses():
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

end_buffer_size = 3

def getMaxLines():
    return stdscr.getmaxyx()[0] - end_buffer_size

line_format = "[%(checkmark)s] %(status)-6s %(file)s"
help_string1 = "q     - quit          | a - check all   | up/down    - move one line"
help_string2 = "space - check/uncheck | u - uncheck all | right/left - page up/down"

def redraw():
    global err
    global page
    maxLines = getMaxLines()
    page = currentLine / maxLines
    start = page * maxLines
    stdscr.erase()
    for linenumber, fileinfo in enumerate(filelist[start:start + maxLines]):
        if fileinfo['checked']:
            fileinfo['checkmark'] = 'x'
        else:
            fileinfo['checkmark'] = ' '
        try:
            stdscr.addstr(linenumber, 0, line_format % fileinfo, curses.A_BOLD)
        except Exception, err:
            logging.error(err)
    if len(filelist) == 0:
        stdscr.addstr(0, 0, "No files changes - press 'q' to quit", curses.A_BOLD)
    else:
        stdscr.addstr(maxLines + 1,     0, help_string1, curses.A_DIM)
        stdscr.addstr(maxLines + 2, 0, help_string2, curses.A_DIM)


def toggleChecked(index):
    checked = filelist[index]["checked"]
    filelist[index]["checked"] = not checked

def checkall(checked=True):
    for file in filelist:
        file["checked"] = checked

def move(amount):
    global currentLine
    if (amount + currentLine < 0):
        currentLine = 0
    elif (amount + currentLine > (len(filelist) - 1)):
        currentLine = len(filelist) - 1
    else:
        currentLine = currentLine + amount
    redraw()
    positionCursor()

def positionCursor():
    stdscr.move((currentLine % getMaxLines()) ,1)

def gotoPage(newPage):
    newLine = newPage * getMaxLines() + (currentLine % getMaxLines())
    move(newLine - currentLine)
    redraw()
    positionCursor()

def main():
    global stdscr
    try:
        global filelist
        # get the file list before initCurses, because opening a pipe
        # after curses is initialized causes Cygwin to hang
        filelist = getFileList()
        initCurses()

        redraw()

        y,x = curses.getsyx()
        stdscr.move(0,1)
        while 1:
            c = stdscr.getch()
            logging.debug(c)
            if c == ord('q'): break  # Exit the while()
            elif c == curses.KEY_UP: 
                logging.debug("KEYUP!")
                move(-1)
            elif c == curses.KEY_DOWN : 
                logging.debug("KEYDOWN")
                move(1)
            elif c == ord(' '):
                logging.debug("SPACE")
                toggleChecked(currentLine)
                move(1)
            elif c == ord('a'):
                y,x = curses.getsyx()
                checkall()
                redraw()
                stdscr.move(y,x)
            elif c == ord('u'):
                y,x = curses.getsyx()
                checkall(False)
                redraw()
                stdscr.move(y,x)
            elif c == curses.KEY_RIGHT: 
                logging.debug("KEY_RIGHT")
                move(getMaxLines())
            elif c == curses.KEY_LEFT: 
                logging.debug("KEY_LEFT")
                move(-getMaxLines())
            elif 0 <= c <= 256 and chr(c).isdigit():
                destination = 10
                if chr(c) != 0:
                    destination = int(chr(c)) - 1
                gotoPage(destination)

    except Exception, err:
        logging.error(err)
    cleanupCurses()
    print " ".join(f["file"] for f in filelist if f["checked"])

if __name__ == "__main__":
    main()
