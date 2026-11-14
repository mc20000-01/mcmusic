#---------------------------------------------------------------------------------
# mcmusic for Nintendo 3DS / 2DS — devkitARM homebrew build
#
#   export DEVKITPRO=/opt/devkitpro
#   make
#
# Produces mcmusic.3dsx. Add an smdh/banner and run makerom for a .cia.
#---------------------------------------------------------------------------------
ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment (usually /opt/devkitpro/devkitARM)")
endif

TOPDIR ?= $(CURDIR)
include $(DEVKITARM)/3ds_rules

TARGET   := mcmusic
BUILD    := build
SOURCES  := source
INCLUDES := include

ARCH     := -march=armv6k -mtune=mpcore -mfloat-abi=hard -mtp=soft

CFLAGS   := -g -Wall -O2 -mword-relocations \
            -ffunction-sections \
            $(ARCH) \
            -I$(CURDIR)/$(INCLUDES) \
            -I$(CTRULIB)/include \
            -D__3DS__

LDFLAGS  := -specs=3dsx.specs -g $(ARCH) \
            -Wl,-Map,$(TARGET).map \
            -L$(CTRULIB)/lib

LIBS     := -lcitro2d -lcitro3d -lctru -lm

CFILES   := $(wildcard $(SOURCES)/*.c)
OFILES   := $(patsubst $(SOURCES)/%.c,$(BUILD)/%.o,$(CFILES))
DEPS     := $(OFILES:.o=.d)

.PHONY: all clean

all: $(TARGET).3dsx

$(BUILD):
	@mkdir -p $@

$(BUILD)/%.o: $(SOURCES)/%.c | $(BUILD)
	$(CC) $(CFLAGS) -MMD -MP -c $< -o $@

$(TARGET).elf: $(OFILES)
	$(CC) $(LDFLAGS) $(OFILES) $(LIBS) -o $@

$(TARGET).3dsx: $(TARGET).elf
	3dsxtool $< $@

clean:
	@rm -rf $(BUILD) $(TARGET).elf $(TARGET).3dsx $(TARGET).map

-include $(DEPS)
