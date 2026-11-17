/****************************************************/
/* File: tm.c                                       */
/* The TM ("Tiny Machine") computer                 */
/* Compiler Construction: Principles and Practice   */
/* Kenneth C. Louden                                */
/*                                                  */
/* Extensión para el compilador CAOS (Fase 4):      */
/*  - registros y memoria de datos en double         */
/*    (CAOS tiene int, float y bool)                */
/*  - LDC acepta constantes reales: LDC 0,3.14(0)   */
/*  - DIV conserva la división entera (trunca)      */
/*  - instrucciones nuevas:                         */
/*      INF   r,0,0   lee un número real            */
/*      OUTF  r,0,0   imprime un real               */
/*      OUTLN 0,0,0   imprime un salto de línea     */
/*      DIVF  r,s,t   división real                 */
/*      POW   r,s,t   reg(r) = reg(s) ^ reg(t)      */
/*      OUTS  r,d(s)  imprime la cadena terminada   */
/*                    en 0 que inicia en d+reg(s)   */
/*  - OUT imprime solo el valor entero, sin texto   */
/*  - los opcodes se comparan con la palabra entera */
/****************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

#ifndef TRUE
#define TRUE 1
#endif
#ifndef FALSE
#define FALSE 0
#endif

/******* const *******/
#define   IADDR_SIZE  8192 /* increase for large programs */
#define   DADDR_SIZE  4096 /* increase for large programs */
#define   NO_REGS 8
#define   PC_REG  7

#define   LINESIZE  256
#define   WORDSIZE  20

/******* type  *******/

typedef enum {
   opclRR,     /* reg operands r,s,t */
   opclRM,     /* reg r, mem d+s */
   opclRA      /* reg r, int d+s */
   } OPCLASS;

typedef enum {
   /* RR instructions */
   opHALT,    /* RR     halt, operands are ignored */
   opIN,      /* RR     read integer into reg(r); s and t are ignored */
   opOUT,     /* RR     write integer from reg(r), s and t are ignored */
   opADD,     /* RR     reg(r) = reg(s)+reg(t) */
   opSUB,     /* RR     reg(r) = reg(s)-reg(t) */
   opMUL,     /* RR     reg(r) = reg(s)*reg(t) */
   opDIV,     /* RR     reg(r) = trunc(reg(s)/reg(t)) */
   opINF,     /* RR     read real into reg(r) */
   opOUTF,    /* RR     write real from reg(r) */
   opOUTLN,   /* RR     write end of line */
   opDIVF,    /* RR     reg(r) = reg(s)/reg(t) (real) */
   opPOW,     /* RR     reg(r) = reg(s)^reg(t) */
   opRRLim,   /* limit of RR opcodes */

   /* RM instructions */
   opLD,      /* RM     reg(r) = mem(d+reg(s)) */
   opST,      /* RM     mem(d+reg(s)) = reg(r) */
   opOUTS,    /* RM     write string mem(d+reg(s)) ... until 0 */
   opRMLim,   /* Limit of RM opcodes */

   /* RA instructions */
   opLDA,     /* RA     reg(r) = d+reg(s) */
   opLDC,     /* RA     reg(r) = d ; reg(s) is ignored */
   opJLT,     /* RA     if reg(r)<0 then reg(7) = d+reg(s) */
   opJLE,     /* RA     if reg(r)<=0 then reg(7) = d+reg(s) */
   opJGT,     /* RA     if reg(r)>0 then reg(7) = d+reg(s) */
   opJGE,     /* RA     if reg(r)>=0 then reg(7) = d+reg(s) */
   opJEQ,     /* RA     if reg(r)==0 then reg(7) = d+reg(s) */
   opJNE,     /* RA     if reg(r)!=0 then reg(7) = d+reg(s) */
   opRALim    /* Limit of RA opcodes */
   } OPCODE;

typedef enum {
   srOKAY,
   srHALT,
   srIMEM_ERR,
   srDMEM_ERR,
   srZERODIVIDE
   } STEPRESULT;

typedef struct {
      int iop  ;
      int iarg1  ;
      double iarg2  ;
      int iarg3  ;
   } INSTRUCTION;

/******** vars ********/
int iloc = 0 ;
int dloc = 0 ;
int traceflag = FALSE;
int icountflag = FALSE;

INSTRUCTION iMem [IADDR_SIZE];
double dMem [DADDR_SIZE];
double reg [NO_REGS];

char * opCodeTab[]
        = {"HALT","IN","OUT","ADD","SUB","MUL","DIV",
           "INF","OUTF","OUTLN","DIVF","POW","????",
            /* RR opcodes */
           "LD","ST","OUTS","????", /* RM opcodes */
           "LDA","LDC","JLT","JLE","JGT","JGE","JEQ","JNE","????"
           /* RA opcodes */
          };

char * stepResultTab[]
        = {"OK","Halted","Instruction Memory Fault",
           "Data Memory Fault","Division by 0"
          };

char pgmName[1024];
FILE *pgm  ;

char in_Line[LINESIZE] ;
int lineLen ;
int inCol  ;
int num  ;
double realNum ;
char word[WORDSIZE] ;
char ch  ;
int done  ;

/* Lectura segura desde consola (reemplaza gets, eliminada en C11). */
static int readConsoleLine(void)
{
  size_t len;
  int chExtra;
  if (!fgets(in_Line, sizeof(in_Line), stdin)) return FALSE;
  len = strcspn(in_Line, "\r\n");
  if (in_Line[len] == '\0' && len == sizeof(in_Line)-1)
  {
    while ((chExtra = getchar()) != '\n' && chExtra != EOF) {}
  }
  in_Line[len] = '\0';
  lineLen = (int)len;
  inCol = 0;
  return TRUE;
}

/* Formato de un real: hasta 6 decimales, sin ceros sobrantes, mínimo x.0 */
static void formatReal(double v, char *buf, size_t size)
{
  char *p;
  if (isnan(v)) { snprintf(buf, size, "nan"); return; }
  if (isinf(v)) { snprintf(buf, size, v > 0 ? "inf" : "-inf"); return; }
  snprintf(buf, size, "%.6f", v);
  p = buf + strlen(buf) - 1;
  while (*p == '0' && *(p-1) != '.') *p-- = '\0';
  if (strcmp(buf, "-0.0") == 0) snprintf(buf, size, "0.0");
}

/* Formato de un valor de memoria o registro para los comandos r y d */
static void formatValue(double v, char *buf, size_t size)
{
  if (v == floor(v) && fabs(v) < 1e15) snprintf(buf, size, "%lld", (long long)v);
  else formatReal(v, buf, size);
}

/********************************************/
int opClass( int c )
{ if      ( c <= opRRLim) return ( opclRR );
  else if ( c <= opRMLim) return ( opclRM );
  else                    return ( opclRA );
} /* opClass */

/********************************************/
void writeInstruction ( int loc )
{ char buf[64];
  printf( "%5d: ", loc) ;
  if ( (loc >= 0) && (loc < IADDR_SIZE) )
  { printf("%6s%3d,", opCodeTab[iMem[loc].iop], iMem[loc].iarg1);
    switch ( opClass(iMem[loc].iop) )
    { case opclRR: printf("%1d,%1d", (int)iMem[loc].iarg2, iMem[loc].iarg3);
                   break;
      case opclRM:
      case opclRA: formatValue(iMem[loc].iarg2, buf, sizeof(buf));
                   printf("%3s(%1d)", buf, iMem[loc].iarg3);
                   break;
    }
    printf ("\n") ;
  }
} /* writeInstruction */

/********************************************/
void getCh (void)
{ if (++inCol < lineLen)
  ch = in_Line[inCol] ;
  else ch = ' ' ;
} /* getCh */

/********************************************/
int nonBlank (void)
{ while ((inCol < lineLen)
         && ((in_Line[inCol] == ' ') || (in_Line[inCol] == '\t')) )
    inCol++ ;
  if (inCol < lineLen)
  { ch = in_Line[inCol] ;
    return TRUE ; }
  else
  { ch = ' ' ;
    return FALSE ; }
} /* nonBlank */

/********************************************/
int getNum (void)
{ int sign;
  int term;
  int temp = FALSE;
  num = 0 ;
  do
  { sign = 1;
    while ( nonBlank() && ((ch == '+') || (ch == '-')) )
    { temp = FALSE ;
      if (ch == '-')  sign = - sign ;
      getCh();
    }
    term = 0 ;
    nonBlank();
    while (isdigit((unsigned char)ch))
    { temp = TRUE ;
      term = term * 10 + ( ch - '0' ) ;
      getCh();
    }
    num = num + (term * sign) ;
  } while ( (nonBlank()) && ((ch == '+') || (ch == '-')) ) ;
  return temp;
} /* getNum */

/* Lee un número real (entero, decimal o con exponente) en realNum */
int getReal (void)
{ char *start;
  char *end;
  if (!nonBlank()) return FALSE;
  start = in_Line + inCol;
  realNum = strtod(start, &end);
  if (end == start) return FALSE;
  inCol += (int)(end - start);
  if (inCol < lineLen) ch = in_Line[inCol]; else ch = ' ';
  return TRUE;
} /* getReal */

/********************************************/
int getWord (void)
{ int temp = FALSE;
  int length = 0;
  if (nonBlank ())
  { while (isalnum((unsigned char)ch))
    { if (length < WORDSIZE-1) word [length++] =  ch ;
      getCh() ;
    }
    word[length] = '\0';
    temp = (length != 0);
  }
  return temp;
} /* getWord */

/********************************************/
int skipCh ( char c  )
{ int temp = FALSE;
  if ( nonBlank() && (ch == c) )
  { getCh();
    temp = TRUE;
  }
  return temp;
} /* skipCh */

/********************************************/
int atEOL(void)
{ return ( ! nonBlank ());
} /* atEOL */

/********************************************/
int error( char * msg, int lineNo, int instNo)
{ printf("Line %d",lineNo);
  if (instNo >= 0) printf(" (Instruction %d)",instNo);
  printf("   %s\n",msg);
  return FALSE;
} /* error */

/********************************************/
int readInstructions (void)
{ OPCODE op;
  int arg1, arg3;
  double arg2;
  int loc, regNo, lineNo;
  for (regNo = 0 ; regNo < NO_REGS ; regNo++)
      reg[regNo] = 0 ;
  dMem[0] = DADDR_SIZE - 1 ;
  for (loc = 1 ; loc < DADDR_SIZE ; loc++)
      dMem[loc] = 0 ;
  for (loc = 0 ; loc < IADDR_SIZE ; loc++)
  { iMem[loc].iop = opHALT ;
    iMem[loc].iarg1 = 0 ;
    iMem[loc].iarg2 = 0 ;
    iMem[loc].iarg3 = 0 ;
  }
  lineNo = 0 ;
  while (fgets(in_Line, sizeof(in_Line), pgm) != NULL)
  {
    lineNo++;
    lineLen = (int)strcspn(in_Line, "\r\n");
    in_Line[lineLen] = '\0';
    inCol = 0;
    if ( (nonBlank()) && (in_Line[inCol] != '*') )
    { if (! getNum())
        return error("Bad location", lineNo,-1);
      loc = num;
      if (loc < 0 || loc >= IADDR_SIZE)
        return error("Location too large",lineNo,loc);
      if (! skipCh(':'))
        return error("Missing colon", lineNo,loc);
      if (! getWord ())
        return error("Missing opcode", lineNo,loc);
      op = opHALT ;
      while ((op < opRALim)
             && (strcmp(opCodeTab[op], word) != 0) )
          op++ ;
      if (op >= opRALim || strcmp(opCodeTab[op], "????") == 0)
          return error("Illegal opcode", lineNo,loc);
      switch ( opClass(op) )
      { case opclRR :
        /***********************************/
        if ( (! getNum ()) || (num < 0) || (num >= NO_REGS) )
            return error("Bad first register", lineNo,loc);
        arg1 = num;
        if ( ! skipCh(','))
            return error("Missing comma", lineNo, loc);
        if ( (! getNum ()) || (num < 0) || (num >= NO_REGS) )
            return error("Bad second register", lineNo, loc);
        arg2 = num;
        if ( ! skipCh(','))
            return error("Missing comma", lineNo,loc);
        if ( (! getNum ()) || (num < 0) || (num >= NO_REGS) )
            return error("Bad third register", lineNo,loc);
        arg3 = num;
        break;

        case opclRM :
        case opclRA :
        default :
        /***********************************/
        if ( (! getNum ()) || (num < 0) || (num >= NO_REGS) )
            return error("Bad first register", lineNo,loc);
        arg1 = num;
        if ( ! skipCh(','))
            return error("Missing comma", lineNo,loc);
        if (! getReal ())
            return error("Bad displacement", lineNo,loc);
        arg2 = realNum;
        if ( ! skipCh('(') && ! skipCh(',') )
            return error("Missing LParen", lineNo,loc);
        if ( (! getNum ()) || (num < 0) || (num >= NO_REGS))
            return error("Bad second register", lineNo,loc);
        arg3 = num;
        break;
        }
      iMem[loc].iop = op;
      iMem[loc].iarg1 = arg1;
      iMem[loc].iarg2 = arg2;
      iMem[loc].iarg3 = arg3;
    }
  }
  return TRUE;
} /* readInstructions */

/* Lee un valor desde consola para IN (entero) o INF (real) */
static int readValue(int isReal, double *out)
{ char *start;
  char *end;
  double v;
  int ok;
  do
  { if (isReal) printf("Enter real value for INF instruction: ");
    else        printf("Enter value for IN instruction: ");
    fflush(stdout);
    if (!readConsoleLine()) return FALSE;
    start = in_Line;
    while (*start == ' ' || *start == '\t') start++;
    v = strtod(start, &end);
    while (*end == ' ' || *end == '\t') end++;
    ok = (end != start) && (*end == '\0') && !isnan(v) && !isinf(v);
    if (ok && !isReal && v != floor(v)) ok = FALSE;
    if (!ok) printf("Illegal value\n");
  } while (!ok);
  *out = v;
  return TRUE;
}

/********************************************/
STEPRESULT stepTM (void)
{ INSTRUCTION currentinstruction  ;
  int pc  ;
  int r=0,s=0,t=0,m=0  ;
  double value;
  char buf[64];

  pc = (int)reg[PC_REG] ;
  if ( (pc < 0) || (pc >= IADDR_SIZE)  )
      return srIMEM_ERR ;
  reg[PC_REG] = pc + 1 ;
  currentinstruction = iMem[ pc ] ;
  switch (opClass(currentinstruction.iop) )
  { case opclRR :
    /***********************************/
      r = currentinstruction.iarg1 ;
      s = (int)currentinstruction.iarg2 ;
      t = currentinstruction.iarg3 ;
      break;

    case opclRM :
    /***********************************/
      r = currentinstruction.iarg1 ;
      s = currentinstruction.iarg3 ;
      m = (int)(currentinstruction.iarg2 + reg[s]) ;
      if ( (m < 0) || (m >= DADDR_SIZE))
         return srDMEM_ERR ;
      break;

    case opclRA :
    /***********************************/
      r = currentinstruction.iarg1 ;
      s = currentinstruction.iarg3 ;
      m = (int)(currentinstruction.iarg2 + reg[s]) ;
      break;
  } /* case */

  switch ( currentinstruction.iop)
  { /* RR instructions */
    case opHALT :
    /***********************************/
      printf("HALT: %1d,%1d,%1d\n",r,s,t);
      return srHALT ;
      /* break; */

    case opIN :
    /***********************************/
      if (!readValue(FALSE, &value)) return srHALT;
      reg[r] = value;
      break;

    case opINF :
    /***********************************/
      if (!readValue(TRUE, &value)) return srHALT;
      reg[r] = value;
      break;

    case opOUT :
      printf ("%lld", (long long)reg[r] ) ;
      fflush(stdout);
      break;
    case opOUTF :
      formatReal(reg[r], buf, sizeof(buf));
      printf ("%s", buf ) ;
      fflush(stdout);
      break;
    case opOUTLN :
      printf ("\n") ;
      fflush(stdout);
      break;
    case opADD :  reg[r] = reg[s] + reg[t] ;  break;
    case opSUB :  reg[r] = reg[s] - reg[t] ;  break;
    case opMUL :  reg[r] = reg[s] * reg[t] ;  break;

    case opDIV :
    /***********************************/
      if ( reg[t] != 0 ) reg[r] = trunc(reg[s] / reg[t]);
      else return srZERODIVIDE ;
      break;

    case opDIVF :
    /***********************************/
      if ( reg[t] != 0 ) reg[r] = reg[s] / reg[t];
      else return srZERODIVIDE ;
      break;

    case opPOW :  reg[r] = pow(reg[s], reg[t]) ;  break;

    /*************** RM instructions ********************/
    case opLD :    reg[r] = dMem[m] ;  break;
    case opST :    dMem[m] = reg[r] ;  break;
    case opOUTS :
      while ( m < DADDR_SIZE && dMem[m] != 0 )
      { putchar((int)dMem[m]);
        m++;
      }
      fflush(stdout);
      if ( m >= DADDR_SIZE ) return srDMEM_ERR ;
      break;

    /*************** RA instructions ********************/
    case opLDA :    reg[r] = m ; break;
    case opLDC :    reg[r] = currentinstruction.iarg2 ;   break;
    case opJLT :    if ( reg[r] <  0 ) reg[PC_REG] = m ; break;
    case opJLE :    if ( reg[r] <=  0 ) reg[PC_REG] = m ; break;
    case opJGT :    if ( reg[r] >  0 ) reg[PC_REG] = m ; break;
    case opJGE :    if ( reg[r] >=  0 ) reg[PC_REG] = m ; break;
    case opJEQ :    if ( reg[r] == 0 ) reg[PC_REG] = m ; break;
    case opJNE :    if ( reg[r] != 0 ) reg[PC_REG] = m ; break;

    /* end of legal instructions */
  } /* case */
  return srOKAY ;
} /* stepTM */

/********************************************/
int doCommand (void)
{ char cmd;
  int stepcnt=0, i;
  int printcnt;
  int stepResult;
  int regNo, loc;
  char buf[64];
  do
  { printf ("Enter command: ");
    fflush(stdout);
    if (!readConsoleLine()) return FALSE;
  }
  while (! getWord ());

  cmd = word[0] ;
  switch ( cmd )
  { case 't' :
    /***********************************/
      traceflag = ! traceflag ;
      printf("Tracing now ");
      if ( traceflag ) printf("on.\n"); else printf("off.\n");
      break;

    case 'h' :
    /***********************************/
      printf("Commands are:\n");
      printf("   s(tep <n>      "\
             "Execute n (default 1) TM instructions\n");
      printf("   g(o            "\
             "Execute TM instructions until HALT\n");
      printf("   r(egs          "\
             "Print the contents of the registers\n");
      printf("   i(Mem <b <n>>  "\
             "Print n iMem locations starting at b\n");
      printf("   d(Mem <b <n>>  "\
             "Print n dMem locations starting at b\n");
      printf("   t(race         "\
             "Toggle instruction trace\n");
      printf("   p(rint         "\
             "Toggle print of total instructions executed"\
             " ('go' only)\n");
      printf("   c(lear         "\
             "Reset simulator for new execution of program\n");
      printf("   h(elp          "\
             "Cause this list of commands to be printed\n");
      printf("   q(uit          "\
             "Terminate the simulation\n");
      break;

    case 'p' :
    /***********************************/
      icountflag = ! icountflag ;
      printf("Printing instruction count now ");
      if ( icountflag ) printf("on.\n"); else printf("off.\n");
      break;

    case 's' :
    /***********************************/
      if ( atEOL ())  stepcnt = 1;
      else if ( getNum ())  stepcnt = abs(num);
      else   printf("Step count?\n");
      break;

    case 'g' :   stepcnt = 1 ;     break;

    case 'r' :
    /***********************************/
      for (i = 0; i < NO_REGS; i++)
      { formatValue(reg[i], buf, sizeof(buf));
        printf("%1d: %4s    ", i, buf);
        if ( (i % 4) == 3 ) printf ("\n");
      }
      break;

    case 'i' :
    /***********************************/
      printcnt = 1 ;
      if ( getNum ())
      { iloc = num ;
        if ( getNum ()) printcnt = num ;
      }
      if ( ! atEOL ())
        printf ("Instruction locations?\n");
      else
      { while ((iloc >= 0) && (iloc < IADDR_SIZE)
                && (printcnt > 0) )
        { writeInstruction(iloc);
          iloc++ ;
          printcnt-- ;
        }
      }
      break;

    case 'd' :
    /***********************************/
      printcnt = 1 ;
      if ( getNum  ())
      { dloc = num ;
        if ( getNum ()) printcnt = num ;
      }
      if ( ! atEOL ())
        printf("Data locations?\n");
      else
      { while ((dloc >= 0) && (dloc < DADDR_SIZE)
                  && (printcnt > 0))
        { formatValue(dMem[dloc], buf, sizeof(buf));
          printf("%5d: %5s\n",dloc,buf);
          dloc++;
          printcnt--;
        }
      }
      break;

    case 'c' :
    /***********************************/
      iloc = 0;
      dloc = 0;
      stepcnt = 0;
      for (regNo = 0;  regNo < NO_REGS ; regNo++)
            reg[regNo] = 0 ;
      dMem[0] = DADDR_SIZE - 1 ;
      for (loc = 1 ; loc < DADDR_SIZE ; loc++)
            dMem[loc] = 0 ;
      break;

    case 'q' : return FALSE;  /* break; */

    default : printf("Command %c unknown.\n", cmd); break;
  }  /* case */
  stepResult = srOKAY;
  if ( stepcnt > 0 )
  { if ( cmd == 'g' )
    { stepcnt = 0;
      while (stepResult == srOKAY)
      { iloc = (int)reg[PC_REG] ;
        if ( traceflag ) writeInstruction( iloc ) ;
        stepResult = stepTM ();
        stepcnt++;
      }
      if ( icountflag )
        printf("Number of instructions executed = %d\n",stepcnt);
    }
    else
    { while ((stepcnt > 0) && (stepResult == srOKAY))
      { iloc = (int)reg[PC_REG] ;
        if ( traceflag ) writeInstruction( iloc ) ;
        stepResult = stepTM ();
        stepcnt-- ;
      }
    }
    printf( "%s\n",stepResultTab[stepResult] );
  }
  return TRUE;
} /* doCommand */


/********************************************/
/* E X E C U T I O N   B E G I N S   H E R E */
/********************************************/

int main( int argc, char * argv[] )
{ if (argc != 2)
  { printf("usage: %s <filename>\n",argv[0]);
    exit(1);
  }
  if (snprintf(pgmName, sizeof(pgmName), "%s", argv[1]) >= (int)sizeof(pgmName))
  {
     fprintf(stderr, "Ruta del archivo demasiado larga.\n");
     return 1;
  }
  {
    const char *base = strrchr(pgmName, '/');
    const char *winbase = strrchr(pgmName, '\\');
    if (winbase && (!base || winbase > base)) base = winbase;
    base = base ? base + 1 : pgmName;
    if (strrchr(base, '.') == NULL)
    {
      if (strlen(pgmName)+4 >= sizeof(pgmName)) return 1;
      strcat(pgmName,".tm");
    }
  }
  pgm = fopen(pgmName,"r");
  if (pgm == NULL)
  { printf("file '%s' not found\n",pgmName);
    exit(1);
  }

  /* read the program */
  if ( ! readInstructions ())
  {
    fclose(pgm);
    return 1;
  }
  fclose(pgm);
  /* switch input file to terminal */
  /* reset( input ); */
  /* read-eval-print */
  printf("TM  simulation (enter h for help)...\n");
  do
     done = ! doCommand ();
  while (! done );
  printf("Simulation done.\n");
  return 0;
}
