--------------------------------------------------------------------------------
--
-- CERN BE-CO-HT         Top level entity for Simple PCIe FMC Carrier
--                       http://www.ohwr.org/projects/spec
--------------------------------------------------------------------------------
--
-- unit name: spec_ddr_test_top (spec_ddr_test_top.vhd)
--
-- author: Matthieu Cattin (matthieu.cattin@cern.ch)
--
-- date: 03-02-2011
--
-- version: 0.1
--
-- description: Top entity for SPEC board.
--
-- dependencies:
--
--------------------------------------------------------------------------------
-- last changes: see svn log.
--------------------------------------------------------------------------------
-- TODO: - 
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.all;
use work.gn4124_core_pkg.all;

library UNISIM;
use UNISIM.vcomponents.all;


entity spec_top is
  generic(
    g_SIMULATION    : string := "FALSE";
    g_CALIB_SOFT_IP : string := "TRUE");
  port
    (
      -- Global ports
      clk_20m_vcxo_i : in std_logic;    -- 20MHz VCXO clock

      --clk_125m_pllref_p_i : in std_logic;  -- 125 MHz PLL reference
      --clk_125m_pllref_n_i : in std_logic;

      -- From GN4124 Local bus
      L_CLKp : in std_logic;            -- Local bus clock (frequency set in GN4124 config registers)
      L_CLKn : in std_logic;            -- Local bus clock (frequency set in GN4124 config registers)

      L_RST_N : in std_logic;           -- Reset from GN4124 (RSTOUT18_N)

      -- General Purpose Interface
      GPIO : inout std_logic_vector(1 downto 0);  -- GPIO[0] -> GN4124 GPIO8
                                                  -- GPIO[1] -> GN4124 GPIO9

      -- PCIe to Local [Inbound Data] - RX
      P2L_RDY    : out std_logic;                      -- Rx Buffer Full Flag
      P2L_CLKn   : in  std_logic;                      -- Receiver Source Synchronous Clock-
      P2L_CLKp   : in  std_logic;                      -- Receiver Source Synchronous Clock+
      P2L_DATA   : in  std_logic_vector(15 downto 0);  -- Parallel receive data
      P2L_DFRAME : in  std_logic;                      -- Receive Frame
      P2L_VALID  : in  std_logic;                      -- Receive Data Valid

      -- Inbound Buffer Request/Status
      P_WR_REQ : in  std_logic_vector(1 downto 0);  -- PCIe Write Request
      P_WR_RDY : out std_logic_vector(1 downto 0);  -- PCIe Write Ready
      RX_ERROR : out std_logic;                     -- Receive Error

      -- Local to Parallel [Outbound Data] - TX
      L2P_DATA   : out std_logic_vector(15 downto 0);  -- Parallel transmit data
      L2P_DFRAME : out std_logic;                      -- Transmit Data Frame
      L2P_VALID  : out std_logic;                      -- Transmit Data Valid
      L2P_CLKn   : out std_logic;                      -- Transmitter Source Synchronous Clock-
      L2P_CLKp   : out std_logic;                      -- Transmitter Source Synchronous Clock+
      L2P_EDB    : out std_logic;                      -- Packet termination and discard

      -- Outbound Buffer Status
      L2P_RDY    : in std_logic;                     -- Tx Buffer Full Flag
      L_WR_RDY   : in std_logic_vector(1 downto 0);  -- Local-to-PCIe Write
      P_RD_D_RDY : in std_logic_vector(1 downto 0);  -- PCIe-to-Local Read Response Data Ready
      TX_ERROR   : in std_logic;                     -- Transmit Error
      VC_RDY     : in std_logic_vector(1 downto 0);  -- Channel ready

      -- Font panel LEDs
      LED_RED   : out std_logic;
      LED_GREEN : out std_logic;
		
      -- I2C interface
      SDA1_b    : inout std_logic;
      SCL1_b    : inout std_logic;

      FPGA_SDA    : inout std_logic;
      FPGA_SCL    : inout std_logic

      -- GPIO ports
		-- THESE PORT CORRESPOND TO 
		
--		  LA33_N : inout std_logic;
--		  LA33_P : inout std_logic; 
--		  LA32_N : inout std_logic;
--		  LA16_P : inout std_logic;
--		  LA15_N : inout std_logic;
--		  LA15_P : inout std_logic;
--		  LA13_P : inout std_logic;
--		  LA13_N : inout std_logic;
--
--		  LA17_P : inout std_logic;
--		  LA14_P : inout std_logic;
--		  LA14_N : inout std_logic;
--		  LA20_N : inout std_logic;
--		  LA20_P : inout std_logic;
--		  LA19_P : inout std_logic;
--		  LA19_N : inout std_logic;
--		  LA17_N : inout std_logic

--		  LA33_N : in std_logic;
--		  LA33_P : in std_logic; 
--		  LA32_N : in std_logic;
--		  LA16_P : in std_logic;
--		  LA15_N : in std_logic;
--		  LA15_P : in std_logic;
--		  LA13_P : in std_logic;
--		  LA13_N : in std_logic;
--
--		  LA17_P : in std_logic;
--		  LA14_P : in std_logic;
--		  LA14_N : in std_logic;
--		  LA20_N : in std_logic;
--		  LA20_P : in std_logic;
--		  LA19_P : in std_logic;
--		  LA19_N : in std_logic;
--		  LA17_N : in std_logic

--		  LA33_N : out std_logic;
--		  LA33_P : out std_logic; 
--		  LA32_N : out std_logic;
--		  LA16_P : out std_logic;
--		  LA15_N : out std_logic;
--		  LA15_P : out std_logic;
--		  LA13_P : out std_logic;
--		  LA13_N : out std_logic;
--
--		  LA17_P : out std_logic;
--		  LA14_P : out std_logic;
--		  LA14_N : out std_logic;
--		  LA20_N : out std_logic;
--		  LA20_P : out std_logic;
--		  LA19_P : out std_logic;
--		  LA19_N : out std_logic;
--		  LA17_N : out std_logic

      );
end spec_top;


architecture rtl of spec_top is

  ------------------------------------------------------------------------------
  -- Components declaration
  ------------------------------------------------------------------------------

  component gn4124_core
    generic(
      g_BAR0_APERTURE     : integer := 20;  -- BAR0 aperture, defined in GN4124 PCI_BAR_CONFIG register (0x80C)
                                            -- => number of bits to address periph on the board
      g_CSR_WB_SLAVES_NB  : integer := 3;   -- Number of CSR wishbone slaves
      g_DMA_WB_SLAVES_NB  : integer := 1;   -- Number of DMA wishbone slaves
      g_DMA_WB_ADDR_WIDTH : integer := 26   -- DMA wishbone address bus width
      );
    port
      (
        ---------------------------------------------------------
        -- Control and status
        --
        -- Asynchronous reset from GN4124
        rst_n_a_i      : in  std_logic;
        -- P2L clock PLL locked
        p2l_pll_locked : out std_logic;
        -- Debug ouputs
        debug_o        : out std_logic_vector(7 downto 0);

        ---------------------------------------------------------
        -- P2L Direction
        --
        -- Source Sync DDR related signals
        p2l_clk_p_i  : in  std_logic;                      -- Receiver Source Synchronous Clock+
        p2l_clk_n_i  : in  std_logic;                      -- Receiver Source Synchronous Clock-
        p2l_data_i   : in  std_logic_vector(15 downto 0);  -- Parallel receive data
        p2l_dframe_i : in  std_logic;                      -- Receive Frame
        p2l_valid_i  : in  std_logic;                      -- Receive Data Valid
        -- P2L Control
        p2l_rdy_o    : out std_logic;                      -- Rx Buffer Full Flag
        p_wr_req_i   : in  std_logic_vector(1 downto 0);   -- PCIe Write Request
        p_wr_rdy_o   : out std_logic_vector(1 downto 0);   -- PCIe Write Ready
        rx_error_o   : out std_logic;                      -- Receive Error

        ---------------------------------------------------------
        -- L2P Direction
        --
        -- Source Sync DDR related signals
        l2p_clk_p_o  : out std_logic;                      -- Transmitter Source Synchronous Clock+
        l2p_clk_n_o  : out std_logic;                      -- Transmitter Source Synchronous Clock-
        l2p_data_o   : out std_logic_vector(15 downto 0);  -- Parallel transmit data
        l2p_dframe_o : out std_logic;                      -- Transmit Data Frame
        l2p_valid_o  : out std_logic;                      -- Transmit Data Valid
        l2p_edb_o    : out std_logic;                      -- Packet termination and discard
        -- L2P Control
        l2p_rdy_i    : in  std_logic;                      -- Tx Buffer Full Flag
        l_wr_rdy_i   : in  std_logic_vector(1 downto 0);   -- Local-to-PCIe Write
        p_rd_d_rdy_i : in  std_logic_vector(1 downto 0);   -- PCIe-to-Local Read Response Data Ready
        tx_error_i   : in  std_logic;                      -- Transmit Error
        vc_rdy_i     : in  std_logic_vector(1 downto 0);   -- Channel ready

        ---------------------------------------------------------
        -- Interrupt interface
        dma_irq_o : out std_logic_vector(1 downto 0);  -- Interrupts sources to IRQ manager
        irq_p_i   : in  std_logic;                     -- Interrupt request pulse from IRQ manager
        irq_p_o   : out std_logic;                     -- Interrupt request pulse to GN4124 GPIO

        ---------------------------------------------------------
        -- Target interface (CSR wishbone master)
        wb_clk_i : in  std_logic;
        wb_adr_o : out std_logic_vector(g_BAR0_APERTURE-log2_ceil(g_CSR_WB_SLAVES_NB+1)-1 downto 0);
        wb_dat_o : out std_logic_vector(31 downto 0);                         -- Data out
        wb_sel_o : out std_logic_vector(3 downto 0);                          -- Byte select
        wb_stb_o : out std_logic;
        wb_we_o  : out std_logic;
        wb_cyc_o : out std_logic_vector(g_CSR_WB_SLAVES_NB-1 downto 0);
        wb_dat_i : in  std_logic_vector((32*g_CSR_WB_SLAVES_NB)-1 downto 0);  -- Data in
        wb_ack_i : in  std_logic_vector(g_CSR_WB_SLAVES_NB-1 downto 0);

        ---------------------------------------------------------
        -- DMA interface (Pipelined wishbone master)
        dma_clk_i   : in  std_logic;
        dma_adr_o   : out std_logic_vector(31 downto 0);
        dma_dat_o   : out std_logic_vector(31 downto 0);                         -- Data out
        dma_sel_o   : out std_logic_vector(3 downto 0);                          -- Byte select
        dma_stb_o   : out std_logic;
        dma_we_o    : out std_logic;
        dma_cyc_o   : out std_logic;                                             --_vector(g_DMA_WB_SLAVES_NB-1 downto 0);
        dma_dat_i   : in  std_logic_vector((32*g_DMA_WB_SLAVES_NB)-1 downto 0);  -- Data in
        dma_ack_i   : in  std_logic;                                             --_vector(g_DMA_WB_SLAVES_NB-1 downto 0);
        dma_stall_i : in  std_logic--_vector(g_DMA_WB_SLAVES_NB-1 downto 0)        -- for pipelined Wishbone
        );
  end component;  --  gn4124_core
  
  -- I2C 
  
  component i2c_master_top is
    generic(
            ARST_LVL : std_logic := '0'                   -- asynchronous reset level
    );
    port   (
            -- wishbone signals
            wb_clk_i      : in  std_logic;                    -- master clock input
            wb_rst_i      : in  std_logic := '0';             -- synchronous active high reset
            arst_i        : in  std_logic := not ARST_LVL;    -- asynchronous reset
            wb_adr_i      : in  std_logic_vector(2 downto 0); -- lower address bits
            wb_dat_i      : in  std_logic_vector(7 downto 0); -- Databus input
            wb_dat_o      : out std_logic_vector(7 downto 0); -- Databus output
            wb_we_i       : in  std_logic;                    -- Write enable input
            wb_stb_i      : in  std_logic;                    -- Strobe signals / core select signal
            wb_cyc_i      : in  std_logic;                    -- Valid bus cycle input
            wb_ack_o      : out std_logic;                    -- Bus cycle acknowledge output
            wb_inta_o     : out std_logic;                    -- interrupt request output signal

            -- i2c lines
            scl_pad_i     : in  std_logic;                    -- i2c clock line input
            scl_pad_o     : out std_logic;                    -- i2c clock line output
            scl_padoen_o  : out std_logic;                    -- i2c clock line output enable, active low
            sda_pad_i     : in  std_logic;                    -- i2c data line input
            sda_pad_o     : out std_logic;                    -- i2c data line output
            sda_padoen_o  : out std_logic                     -- i2c data line output enable, active low
    );
  end component; -- i2c_master_top

  component monostable is
  generic(
    g_INPUT_POLARITY  : std_logic := '1';    --! trigger_i polarity
                                             --! ('0'=negative, 1=positive)
    g_OUTPUT_POLARITY : std_logic := '1';    --! pulse_o polarity
                                             --! ('0'=negative, 1=positive)
    g_OUTPUT_RETRIG   : boolean   := false;  --! Retriggerable output monostable
    g_OUTPUT_LENGTH   : natural   := 1       --! pulse_o lenght (in clk_i ticks)
    );
  port (
    rst_n_i   : in  std_logic;               --! Reset (active low)
    clk_i     : in  std_logic;               --! Clock
    trigger_i : in  std_logic;               --! Trigger input pulse
    pulse_o   : out std_logic                --! Monostable output pulse
    );
  end component;
  
  ------------------------------------------------------------------------------
  -- Constants declaration
  ------------------------------------------------------------------------------
  constant c_BAR0_APERTURE     : integer := 20;
  constant c_CSR_WB_SLAVES_NB  : integer := 3;
  constant c_DMA_WB_SLAVES_NB  : integer := 1;
  constant c_DMA_WB_ADDR_WIDTH : integer := 26;

  ------------------------------------------------------------------------------
  -- Signals declaration
  ------------------------------------------------------------------------------

  -- System clock
  signal sys_clk_in         : std_logic;
  signal sys_clk_50_buf     : std_logic;
  signal sys_clk_200_buf    : std_logic;
  signal sys_clk_50         : std_logic;
  signal sys_clk_200        : std_logic;
  signal sys_clk_fb         : std_logic;
  signal sys_clk_pll_locked : std_logic;

  -- LCLK from GN4124 used as system clock
  signal l_clk : std_logic;

  -- P2L clock PLL status
  signal p2l_pll_locked : std_logic;

  -- Reset
  signal rst : std_logic;

  -- CSR wishbone bus
  signal wb_adr     : std_logic_vector(c_BAR0_APERTURE-log2_ceil(c_CSR_WB_SLAVES_NB+1)-1 downto 0);
  signal wb_dat_i   : std_logic_vector((32*c_CSR_WB_SLAVES_NB)-1 downto 0);
  signal wb_dat_o   : std_logic_vector(31 downto 0);
  signal wb_sel     : std_logic_vector(3 downto 0);
  signal wb_cyc     : std_logic_vector(c_CSR_WB_SLAVES_NB-1 downto 0);
  signal wb_stb     : std_logic;
  signal wb_we      : std_logic;
  signal wb_ack     : std_logic_vector(c_CSR_WB_SLAVES_NB-1 downto 0);
  signal spi_wb_adr : std_logic_vector(4 downto 0);

  -- I2C additional signals
  signal scl_fmc_int_in  : std_logic;
  signal scl_fmc_int_out : std_logic;
  signal scl_fmc_int_oe  : std_logic;
  signal sda_fmc_int_in  : std_logic;
  signal sda_fmc_int_out : std_logic;
  signal sda_fmc_int_oe  : std_logic;
  
  signal scl_fmc_int2_in  : std_logic;
  signal scl_fmc_int2_out : std_logic;
  signal scl_fmc_int2_oe  : std_logic;
  signal sda_fmc_int2_in  : std_logic;
  signal sda_fmc_int2_out : std_logic;
  signal sda_fmc_int2_oe  : std_logic;


  -- DMA wishbone bus
  signal dma_adr     : std_logic_vector(31 downto 0);
  signal dma_dat_i   : std_logic_vector((32*c_DMA_WB_SLAVES_NB)-1 downto 0);
  signal dma_dat_o   : std_logic_vector(31 downto 0);
  signal dma_sel     : std_logic_vector(3 downto 0);
  signal dma_cyc     : std_logic;       --_vector(c_DMA_WB_SLAVES_NB-1 downto 0);
  signal dma_stb     : std_logic;
  signal dma_we      : std_logic;
  signal dma_ack     : std_logic;       --_vector(c_DMA_WB_SLAVES_NB-1 downto 0);
  signal dma_stall   : std_logic;       --_vector(c_DMA_WB_SLAVES_NB-1 downto 0);
  signal ram_we      : std_logic_vector(0 downto 0);
  signal ddr_dma_adr : std_logic_vector(29 downto 0);

  -- Interrupts stuff
  signal irq_sources       : std_logic_vector(1 downto 0);
  signal irq_to_gn4124     : std_logic;
  signal irq_sources_2_led : std_logic_vector(1 downto 0);

  -- CSR wishbone slaves for test
  signal gpio_stat     : std_logic_vector(31 downto 0);
  signal gpio_ctrl_1   : std_logic_vector(31 downto 0);
  signal gpio_ctrl_2   : std_logic_vector(31 downto 0);
  signal gpio_ctrl_3   : std_logic_vector(31 downto 0);
  signal gpio_led_ctrl : std_logic_vector(31 downto 0);

  -- SIG: test leds
  signal led_clock : std_logic;
  signal led_1 : std_logic := '0';
  signal led_2 : std_logic := '1';
  
begin


  ------------------------------------------------------------------------------
  -- Clocks distribution from 20MHz TCXO
  --  50.000 MHz system clock
  -- 200.000 MHz fast system clock
  -- 333.333 MHz DDR3 clock
  ------------------------------------------------------------------------------
  cmp_sys_clk_buf : IBUFG
    port map (
      I => clk_20m_vcxo_i,
      O => sys_clk_in);

  cmp_sys_clk_pll : PLL_BASE
    generic map (
      BANDWIDTH          => "OPTIMIZED",
      CLK_FEEDBACK       => "CLKFBOUT",
      COMPENSATION       => "INTERNAL",
      DIVCLK_DIVIDE      => 1,
      CLKFBOUT_MULT      => 50,
      CLKFBOUT_PHASE     => 0.000,
      CLKOUT0_DIVIDE     => 20,
      CLKOUT0_PHASE      => 0.000,
      CLKOUT0_DUTY_CYCLE => 0.500,
      CLKOUT1_DIVIDE     => 5,
      CLKOUT1_PHASE      => 0.000,
      CLKOUT1_DUTY_CYCLE => 0.500,
      CLKOUT2_DIVIDE     => 3,
      CLKOUT2_PHASE      => 0.000,
      CLKOUT2_DUTY_CYCLE => 0.500,
      CLKIN_PERIOD       => 50.0,
      REF_JITTER         => 0.016)
    port map (
      CLKFBOUT => sys_clk_fb,
      CLKOUT0  => sys_clk_50_buf,
      CLKOUT1  => open, --sys_clk_200_buf,
      CLKOUT2  => open,
      CLKOUT3  => open,
      CLKOUT4  => open,
      CLKOUT5  => open,
      LOCKED   => sys_clk_pll_locked,
      RST      => '0',
      CLKFBIN  => sys_clk_fb,
      CLKIN    => sys_clk_in);

  cmp_clk_50_buf : BUFG
    port map (
      O => sys_clk_50,
      I => sys_clk_50_buf);

  --cmp_clk_200_buf : BUFG
  --  port map (
  --    O => sys_clk_200,
  --    I => sys_clk_200_buf);

  ------------------------------------------------------------------------------
  -- Local clock from gennum LCLK
  ------------------------------------------------------------------------------
  cmp_l_clk_buf : IBUFDS
    generic map (
      DIFF_TERM    => false,            -- Differential Termination
      IBUF_LOW_PWR => true,             -- Low power (TRUE) vs. performance (FALSE) setting for referenced I/O standards
      IOSTANDARD   => "DEFAULT")
    port map (
      O  => l_clk,                      -- Buffer output
      I  => L_CLKp,                     -- Diff_p buffer input (connect directly to top-level port)
      IB => L_CLKn                      -- Diff_n buffer input (connect directly to top-level port)
      );

  ------------------------------------------------------------------------------
  -- Active high reset
  ------------------------------------------------------------------------------
  rst <= not(L_RST_N);

  ------------------------------------------------------------------------------
  -- GN4124 interface
  ------------------------------------------------------------------------------
  cmp_gn4124_core : gn4124_core
    generic map (
      g_BAR0_APERTURE     => c_BAR0_APERTURE,
      g_CSR_WB_SLAVES_NB  => c_CSR_WB_SLAVES_NB,
      g_DMA_WB_SLAVES_NB  => c_DMA_WB_SLAVES_NB,
      g_DMA_WB_ADDR_WIDTH => c_DMA_WB_ADDR_WIDTH)
    port map(
      ---------------------------------------------------------
      -- Control and status
      --
      -- Asynchronous reset from GN4124
      rst_n_a_i      => L_RST_N,
      -- P2L clock PLL locked
      p2l_pll_locked => p2l_pll_locked,
      -- Debug outputs
      debug_o        => open,

      ---------------------------------------------------------
      -- P2L Direction
      --
      -- Source Sync DDR related signals
      p2l_clk_p_i  => P2L_CLKp,
      p2l_clk_n_i  => P2L_CLKn,
      p2l_data_i   => P2L_DATA,
      p2l_dframe_i => P2L_DFRAME,
      p2l_valid_i  => P2L_VALID,

      -- P2L Control
      p2l_rdy_o  => P2L_RDY,
      p_wr_req_i => P_WR_REQ,
      p_wr_rdy_o => P_WR_RDY,
      rx_error_o => RX_ERROR,

      ---------------------------------------------------------
      -- L2P Direction
      --
      -- Source Sync DDR related signals
      l2p_clk_p_o  => L2P_CLKp,
      l2p_clk_n_o  => L2P_CLKn,
      l2p_data_o   => L2P_DATA,
      l2p_dframe_o => L2P_DFRAME,
      l2p_valid_o  => L2P_VALID,
      l2p_edb_o    => L2P_EDB,

      -- L2P Control
      l2p_rdy_i    => L2P_RDY,
      l_wr_rdy_i   => L_WR_RDY,
      p_rd_d_rdy_i => P_RD_D_RDY,
      tx_error_i   => TX_ERROR,
      vc_rdy_i     => VC_RDY,

      ---------------------------------------------------------
      -- Interrupt interface
      dma_irq_o => irq_sources,
      irq_p_i   => irq_to_gn4124,
      irq_p_o   => GPIO(0),

      ---------------------------------------------------------
      -- CSR wishbone interface
      wb_clk_i => sys_clk_50,
      wb_adr_o => wb_adr,
      wb_dat_o => wb_dat_o,
      wb_sel_o => wb_sel,
      wb_stb_o => wb_stb,
      wb_we_o  => wb_we,
      wb_cyc_o => wb_cyc,
      wb_dat_i => wb_dat_i,
      wb_ack_i => wb_ack,

      ---------------------------------------------------------
      -- DMA wishbone interface (pipelined)
      dma_clk_i   => sys_clk_50,
      dma_adr_o   => dma_adr,
      dma_dat_o   => dma_dat_o,
      dma_sel_o   => dma_sel,
      dma_stb_o   => dma_stb,
      dma_we_o    => dma_we,
      dma_cyc_o   => dma_cyc,
      dma_dat_i   => dma_dat_i,
      dma_ack_i   => dma_ack,
      dma_stall_i => dma_stall);

  ------------------------------------------------------------------------------
  -- CSR wishbone bus slaves
  --  0 -> I2C controller
  --  1 -> GPIO port
  --  2 -> Not connected
  ------------------------------------------------------------------------------

  ------------------------------------------------------------------------------
  -- Interrupt stuff
  ------------------------------------------------------------------------------
  -- just forward irq pulses for test
  irq_to_gn4124 <= irq_sources(1) or irq_sources(0);

  ------------------------------------------------------------------------------
  -- Assign unused outputs
  ------------------------------------------------------------------------------
  GPIO(1) <= '0';
  
  ----------------------------------------------------------
  -- I2C master
  ----------------------------------------------------------
  I2C_FMC : i2c_master_top
  generic map (
    ARST_LVL => '0')
  port map (
    wb_clk_i     => sys_clk_50,
    wb_rst_i     => rst,
    arst_i       => '1',
    wb_adr_i     => wb_adr(2 downto 0),
    wb_dat_i     => wb_dat_o(7 downto 0),
    wb_dat_o     => wb_dat_i(39 downto 32),  
    wb_we_i      => wb_we,
    wb_stb_i     => wb_stb,
    wb_cyc_i     => wb_cyc(1),
    wb_ack_o     => wb_ack(1),
    wb_inta_o    => open,
    scl_pad_i    => scl_fmc_int2_in,
    scl_pad_o    => scl_fmc_int2_out,
    scl_padoen_o => scl_fmc_int2_oe,
    sda_pad_i    => sda_fmc_int2_in,
    sda_pad_o    => sda_fmc_int2_out,
    sda_padoen_o => sda_fmc_int2_oe);

   SCL1_b      <= scl_fmc_int2_out when (scl_fmc_int2_oe = '0') else 'Z';
  scl_fmc_int2_in <= SCL1_b;

  SDA1_b      <= sda_fmc_int2_out when (sda_fmc_int2_oe = '0') else 'Z';
  sda_fmc_int2_in <= SDA1_b;



  I2C_FMC_2 : i2c_master_top
  generic map (
    ARST_LVL => '0')
  port map (
    wb_clk_i     => sys_clk_50,
    wb_rst_i     => rst,
    arst_i       => '1',
    wb_adr_i     => wb_adr(2 downto 0),
    wb_dat_i     => wb_dat_o(7 downto 0),
    wb_dat_o     => wb_dat_i(7 downto 0),  
    wb_we_i      => wb_we,
    wb_stb_i     => wb_stb,
    wb_cyc_i     => wb_cyc(0),
    wb_ack_o     => wb_ack(0),
    wb_inta_o    => open,
    scl_pad_i    => scl_fmc_int_in,
    scl_pad_o    => scl_fmc_int_out,
    scl_padoen_o => scl_fmc_int_oe,
    sda_pad_i    => sda_fmc_int_in,
    sda_pad_o    => sda_fmc_int_out,
    sda_padoen_o => sda_fmc_int_oe);

  FPGA_SCL      <= scl_fmc_int_out when (scl_fmc_int_oe = '0') else 'Z';
  scl_fmc_int_in <= FPGA_SCL;

  FPGA_SDA      <= sda_fmc_int_out when (sda_fmc_int_oe = '0') else 'Z';
  sda_fmc_int_in <= FPGA_SDA;


 
end rtl;
